"""
Memory Manager - Central hub for all conversation memory operations.
All memory context flows through this module.

Provides:
  - Token-budgeted conversation history
  - Rolling session summarization
  - Cross-session retrieval (via pgvector)
  - User preference learning (from feedback + interactions)
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.config import MEMORY_CONFIG, PG_CONFIG
from backend.ai_agent.token_counter import (
    estimate_tokens,
    truncate_to_tokens,
    truncate_messages_to_budget,
)

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Singleton memory manager.
    All agents should use this instead of accessing conversation tables directly.
    """
    _instance: Optional["MemoryManager"] = None

    @classmethod
    def get_instance(cls) -> "MemoryManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if MemoryManager._instance is not None:
            raise Exception("Use get_instance() or get_memory_manager()")
        self._engine = None
        self._config = MEMORY_CONFIG
        self._init_engine()

    def _init_engine(self):
        """Get shared SQLAlchemy engine from DatabaseService."""
        try:
            from backend.ai_agent.database_service import get_engine
            self._engine = get_engine()
            if self._engine:
                logger.info("[MEMORY] MemoryManager connected to database")
            else:
                logger.warning("[MEMORY] MemoryManager: engine is None – memory features degraded")
        except Exception as e:
            logger.error(f"[MEMORY] Failed to init engine: {e}")

    def _ensure_engine(self) -> bool:
        if self._engine is None:
            self._init_engine()
        return self._engine is not None

    # ──────────────────────────────────────────────────────────────
    # PUBLIC API
    # ──────────────────────────────────────────────────────────────

    def build_memory_context(
        self,
        query: str,
        session_id: str,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Build the complete memory context for an LLM call.
        Returns:
            {
                "conversation_history": List[Dict],   # recent messages
                "session_summary": str,                # rolling summary
                "cross_session_context": str,          # related past sessions
                "user_preferences": str,               # learned preferences
            }
        """
        history = self._get_recent_history(session_id, user_id)
        summary = self._get_session_summary(session_id) if self._config.get("enable_summarization") else ""
        cross_session = ""
        if self._config.get("enable_cross_session"):
            cross_session = self._get_cross_session_context(query, user_id, session_id)
        preferences = ""
        if self._config.get("enable_user_preferences"):
            preferences = self._get_user_preferences(user_id)

        hist_tokens = sum(estimate_tokens(m.get("content", "")) for m in history)
        logger.info(
            f"[MEMORY] Session {session_id[:8]}...: "
            f"{len(history)} messages, {hist_tokens}/{self._config['history_token_budget']} tokens used"
        )
        return {
            "conversation_history": history,
            "session_summary": summary,
            "cross_session_context": cross_session,
            "user_preferences": preferences,
        }

    def trigger_memory_update(
        self,
        query: str,
        response_text: str,
        session_id: str,
        user_id: int,
    ):
        """
        Post-response memory update (summarization + preference extraction).
        Runs synchronously to keep it simple; callers can fire-and-forget via asyncio.
        """
        try:
            if self._config.get("enable_summarization"):
                self._maybe_summarize_session(session_id, user_id)
        except Exception as e:
            logger.error(f"[MEMORY] Summarization error: {e}")

    # ──────────────────────────────────────────────────────────────
    # CONVERSATION HISTORY (token-budgeted)
    # ──────────────────────────────────────────────────────────────

    def _get_recent_history(
        self, session_id: str, user_id: int
    ) -> List[Dict[str, str]]:
        """
        Load recent messages from conversations table, trimmed to token budget.
        """
        if not self._ensure_engine():
            return []

        budget = self._config.get("history_token_budget", 1500)

        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                rows = conn.execute(
                    text(
                        'SELECT query, response, "timestamp" '
                        'FROM conversations '
                        'WHERE conversation_id = :sid AND user_id = :uid '
                        '  AND feedback IS DISTINCT FROM \'negative\' '
                        'ORDER BY "timestamp" ASC'
                    ),
                    {"sid": session_id, "uid": user_id},
                ).fetchall()

            # Build alternating user/assistant messages
            messages: List[Dict[str, str]] = []
            for row in rows:
                messages.append({"role": "user", "content": row[0] or ""})
                messages.append({"role": "assistant", "content": row[1] or ""})

            # Trim to budget
            trimmed = truncate_messages_to_budget(messages, budget)
            return trimmed

        except Exception as e:
            logger.error(f"[MEMORY] Error loading history: {e}")
            return []

    # ──────────────────────────────────────────────────────────────
    # ROLLING SUMMARIZATION
    # ──────────────────────────────────────────────────────────────

    def _get_session_summary(self, session_id: str) -> str:
        """Load the rolling summary for a session."""
        if not self._ensure_engine():
            return ""
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                row = conn.execute(
                    text(
                        "SELECT summary FROM session_summaries "
                        "WHERE session_id = :sid LIMIT 1"
                    ),
                    {"sid": session_id},
                ).fetchone()
            return row[0] if row else ""
        except Exception as e:
            logger.error(f"[MEMORY] Error loading summary: {e}")
            return ""

    def _maybe_summarize_session(self, session_id: str, user_id: int):
        """
        Check if the session has accumulated enough new turns to warrant
        a summary update.  If so, call the LLM to produce a summary.
        """
        if not self._ensure_engine():
            return

        every_n = self._config.get("summarize_every_n_turns", 3)

        try:
            from sqlalchemy import text

            # Count total messages in this session
            with self._engine.connect() as conn:
                count_row = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM conversations "
                        "WHERE conversation_id = :sid AND user_id = :uid "
                        "  AND feedback IS DISTINCT FROM 'negative'"
                    ),
                    {"sid": session_id, "uid": user_id},
                ).fetchone()
                total_messages = count_row[0] if count_row else 0

                # Get current summary state
                sum_row = conn.execute(
                    text(
                        "SELECT message_count FROM session_summaries "
                        "WHERE session_id = :sid LIMIT 1"
                    ),
                    {"sid": session_id},
                ).fetchone()
                summarized_count = sum_row[0] if sum_row else 0

            new_turns = total_messages - summarized_count
            if new_turns < every_n:
                return  # Not enough new turns

            logger.info(
                f"[MEMORY] Session {session_id[:8]}... needs summarization "
                f"({new_turns} new turns)"
            )

            # Get all messages for summarization
            with self._engine.connect() as conn:
                rows = conn.execute(
                    text(
                        'SELECT query, response FROM conversations '
                        'WHERE conversation_id = :sid AND user_id = :uid '
                        '  AND feedback IS DISTINCT FROM \'negative\' '
                        'ORDER BY "timestamp" ASC'
                    ),
                    {"sid": session_id, "uid": user_id},
                ).fetchall()

            conversation_text = "\n".join(
                f"User: {r[0]}\nAssistant: {r[1]}" for r in rows
            )

            # Call LLM for summary
            summary = self._call_llm_for_summary(conversation_text, session_id)

            if summary:
                self._upsert_session_summary(session_id, user_id, summary, total_messages)
                logger.info(f"[MEMORY] Summarized session {session_id[:8]}...")

        except Exception as e:
            logger.error(f"[MEMORY] Summarization error: {e}")

    def _call_llm_for_summary(self, conversation_text: str, session_id: str) -> str:
        """Use Ollama to produce a concise summary of the conversation so far."""
        try:
            import ollama
            from backend.config import AI_CONFIG

            # Truncate very long conversations to avoid context overflow
            max_chars = 4000
            if len(conversation_text) > max_chars:
                conversation_text = conversation_text[:max_chars] + "\n...[truncated]"

            prompt = (
                "Summarize the following conversation concisely. "
                "Capture the key topics, questions asked, data insights revealed, "
                "and any decisions made. Keep it under 200 words. "
                "Write in the same language as the conversation.\n\n"
                f"{conversation_text}"
            )

            response = ollama.chat(
                model=AI_CONFIG.get("ollama_model", "gemma3:latest"),
                messages=[{"role": "user", "content": prompt}],
                options={"num_predict": 256, "temperature": 0.3},
                keep_alive="5m",
            )
            return response["message"]["content"].strip()
        except Exception as e:
            logger.error(f"[MEMORY] LLM summary call failed: {e}")
            return ""

    def _upsert_session_summary(
        self, session_id: str, user_id: int, summary: str, message_count: int
    ):
        """Insert or update session summary in the database."""
        if not self._ensure_engine():
            return
        try:
            from sqlalchemy import text
            # Truncate summary to budget
            budget = self._config.get("summary_token_budget", 300)
            summary = truncate_to_tokens(summary, budget)

            with self._engine.connect() as conn:
                conn.execute(
                    text(
                        "INSERT INTO session_summaries "
                        "(session_id, user_id, summary, message_count, last_summarized_at) "
                        "VALUES (:sid, :uid, :summary, :count, :ts) "
                        "ON CONFLICT (session_id) DO UPDATE SET "
                        "summary = :summary, message_count = :count, last_summarized_at = :ts"
                    ),
                    {
                        "sid": session_id,
                        "uid": user_id,
                        "summary": summary,
                        "count": message_count,
                        "ts": datetime.now(),
                    },
                )
                conn.commit()
        except Exception as e:
            logger.error(f"[MEMORY] Error upserting summary: {e}")

    # ──────────────────────────────────────────────────────────────
    # CROSS-SESSION RETRIEVAL
    # ──────────────────────────────────────────────────────────────

    def _get_cross_session_context(
        self, query: str, user_id: int, current_session_id: str
    ) -> str:
        """
        Find relevant past conversations from OTHER sessions using pgvector
        semantic search on the conversations table embedding column.
        """
        if not self._ensure_engine():
            return ""

        top_k = self._config.get("cross_session_top_k", 3)
        budget = self._config.get("cross_session_token_budget", 400)

        try:
            from backend.ai_agent.vector_service import get_vector_service
            vector_svc = get_vector_service()

            if not vector_svc or not vector_svc._ready:
                return ""

            # Generate embedding for the query
            query_embedding = vector_svc._generate_embedding(query)
            if query_embedding is None:
                return ""

            from sqlalchemy import text
            with self._engine.connect() as conn:
                rows = conn.execute(
                    text(
                        "SELECT query, response, conversation_id "
                        "FROM conversations "
                        "WHERE user_id = :uid "
                        "  AND conversation_id != :sid "
                        "  AND embedding IS NOT NULL "
                        "ORDER BY embedding <=> cast(:emb as vector) "
                        "LIMIT :k"
                    ),
                    {
                        "uid": user_id,
                        "sid": current_session_id,
                        "emb": str(query_embedding),
                        "k": top_k,
                    },
                ).fetchall()

            if not rows:
                return ""

            # Format cross-session matches
            parts = []
            for row in rows:
                parts.append(f"Q: {row[0]}\nA: {row[1]}")

            cross_text = "\n---\n".join(parts)
            cross_text = truncate_to_tokens(cross_text, budget)

            logger.info(
                f"[MEMORY] Found {len(rows)} cross-session matches "
                f"({estimate_tokens(cross_text)} tokens)"
            )
            return cross_text

        except Exception as e:
            logger.error(f"[MEMORY] Cross-session retrieval error: {e}")
            return ""

    # ──────────────────────────────────────────────────────────────
    # USER PREFERENCES
    # ──────────────────────────────────────────────────────────────

    def _get_user_preferences(self, user_id: int) -> str:
        """Load user preferences from user_preferences table."""
        if not self._ensure_engine():
            return ""

        max_prefs = self._config.get("max_preferences", 10)

        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                rows = conn.execute(
                    text(
                        "SELECT preference_key, preference_value, confidence "
                        "FROM user_preferences "
                        "WHERE user_id = :uid "
                        "ORDER BY confidence DESC, updated_at DESC "
                        "LIMIT :limit"
                    ),
                    {"uid": user_id, "limit": max_prefs},
                ).fetchall()

            if not rows:
                return ""

            prefs = []
            for row in rows:
                prefs.append(f"- {row[0]}: {row[1]}")

            pref_text = "\n".join(prefs)
            logger.info(f"[MEMORY] Loaded {len(rows)} preferences for user {user_id}")
            return pref_text

        except Exception as e:
            logger.error(f"[MEMORY] Error loading preferences: {e}")
            return ""

    def extract_preferences_from_feedback(
        self, user_id: int, rating: str, query: str, response: str, comment: Optional[str] = None
    ):
        """
        Learn user preferences from feedback.
        Positive feedback → infer what the user liked.
        Negative feedback with comment → infer what to avoid.
        """
        if not self._config.get("enable_feedback_learning"):
            return
        if not self._ensure_engine():
            return

        try:
            prefs_to_store = []

            # Detect language preference from query
            from backend.ai_agent.llm_service import LLMService
            is_arabic = LLMService.ARABIC_PATTERN.search(query)

            if rating == "positive":
                # Infer language preference
                if is_arabic:
                    prefs_to_store.append(
                        ("preferred_language", "Arabic", "feedback", 0.8)
                    )
                else:
                    prefs_to_store.append(
                        ("preferred_language", "English", "feedback", 0.8)
                    )

                # If response has tables/charts → user likes structured data
                if any(kw in response.lower() for kw in ["table", "chart", "جدول", "رسم"]):
                    prefs_to_store.append(
                        ("prefers_structured_data", "true", "feedback", 0.6)
                    )

            elif rating == "negative" and comment:
                # Store negative feedback as preference to avoid
                prefs_to_store.append(
                    ("feedback_improvement", comment[:200], "feedback", 0.7)
                )

            # Upsert preferences
            for key, value, source, confidence in prefs_to_store:
                self._upsert_preference(user_id, key, value, source, confidence)

        except Exception as e:
            logger.error(f"[MEMORY] Preference extraction error: {e}")

    def _upsert_preference(
        self,
        user_id: int,
        key: str,
        value: str,
        source: str = "inferred",
        confidence: float = 0.5,
    ):
        """Insert or update a user preference."""
        if not self._ensure_engine():
            return
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                conn.execute(
                    text(
                        "INSERT INTO user_preferences "
                        "(user_id, preference_key, preference_value, source, confidence, updated_at) "
                        "VALUES (:uid, :key, :val, :src, :conf, :ts) "
                        "ON CONFLICT (user_id, preference_key) DO UPDATE SET "
                        "preference_value = :val, source = :src, "
                        "confidence = GREATEST(user_preferences.confidence, :conf), "
                        "updated_at = :ts"
                    ),
                    {
                        "uid": user_id,
                        "key": key,
                        "val": value,
                        "src": source,
                        "conf": confidence,
                        "ts": datetime.now(),
                    },
                )
                conn.commit()
        except Exception as e:
            logger.error(f"[MEMORY] Error upserting preference: {e}")


# ── Singleton accessor ────────────────────────────────────────────

_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create the global MemoryManager singleton."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager.get_instance()
    return _memory_manager
