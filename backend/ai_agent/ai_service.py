"""
AI Service - Main entry point for AI agent functionality
Integrates LangGraph multi-agent workflow with domain routing
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.ai_agent.data_adapter import get_adapter
from backend.ai_agent.auth_service import get_auth_service
from backend.config import LANGGRAPH_CONFIG, AI_CONFIG

logger = logging.getLogger(__name__)


class AIService:
    """Main AI Service for processing queries"""
    
    def __init__(self):
        self.adapter = get_adapter()
        self.auth_service = get_auth_service()
        self._conversation_history: Dict[int, List[Dict]] = {}
        logger.info("AIService initialized")
    
    async def process_query(
        self,
        query: str,
        user_id: int,
        conversation_id: Optional[str] = None,
        report_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent pipeline
        """
        start_time = datetime.now()
        
        if not conversation_id:
            conversation_id = f"session_{int(datetime.now().timestamp() * 1000)}"
            
        try:
            from backend.ai_agent.agents.visualization_agent import VisualizationAgent
            
            # ── 1. If report_name is provided, execute SQL directly and skip agents ──
            if report_name:
                import os
                try:
                    # Construct path to the report
                    report_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "data", "reports", f"{report_name}.sql"
                    )
                    
                    if os.path.exists(report_path):
                        with open(report_path, "r", encoding="utf-8") as f:
                            sql_query = f.read()
                            
                        logger.info(f"Direct report execution for {report_name}")
                        raw_data = self.adapter.execute_query(sql_query)
                        
                        # Mock thinking and processing results to feed into the pipeline
                        thinking_result = {
                            "intent": f"execute_report_{report_name}",
                            "required_domains": ["direct_sql_execution"],
                            "tool": "sql",
                        }
                        
                        processing_result = {
                            "data": raw_data,
                            "row_count": len(raw_data),
                            "generated_query": sql_query,
                            "tool_used": "direct_sql",
                            "success": True
                        }
                        
                        access_validation = {
                            "allowed_agents": ["direct_sql_execution"],
                            "blocked_agents": [],
                            "has_access": True,
                            "partial_access": False
                        }
                        
                        # ── Generate visualization for direct reports ──
                        visualization = await VisualizationAgent().generate(
                            query=query or report_name,
                            data=raw_data
                        )

                        # Provide a rudimentary final_response here since we skip the coordinator
                        final_response = {
                            "answer": f"تم جلب بيانات التقرير بنجاح.",
                            "metadata": {}
                        }
                        
                    else:
                        raise FileNotFoundError(f"Report {report_name}.sql not found at {report_path}")
                        
                except Exception as e:
                    logger.error(f"Failed to execute direct report {report_name}: {e}")
                    return {
                        "answer": f"Sorry, I could not generate the {report_name} report. Error: {str(e)}",
                        "error": True,
                        "metadata": {}
                    }
                    
            # ── 2. Otherwise route query via normal agents ──
            else:
                # Bypass agent checks for now as requested by user
                all_agents = self.auth_service.get_all_domain_agents()
                user_agents = [a.get("code", "") for a in all_agents]
                
                # Route query to determine required domains
                from backend.ai_agent.agents.thinking_agent import ThinkingAgent
                thinking_agent = ThinkingAgent()
                thinking_result = await thinking_agent.analyze(query, user_agents)
                
                # Validate access bypass
                required_domains = thinking_result.get("required_domains", [])
                
                access_validation = {
                    "allowed_agents": required_domains if required_domains else user_agents,
                    "blocked_agents": [],
                    "has_access": True,
                    "partial_access": False
                }
                
                # --- 2.5. Query Safety Check ---
                from backend.ai_agent.query_safety_guard import QuerySafetyGuard
                safety_result = QuerySafetyGuard.check(query, thinking_result)
                
                if safety_result["safety_level"] == "BLOCK":
                    # Short-circuit everything and return a clarification response
                    logger.warning(f"Query blocked by SafetyGuard: {query}")
                    final_response = {
                        "answer": f"{safety_result['block_reason']}\n\nمقترح: {safety_result['suggested_query']}",
                        "needs_clarification": True,
                        "suggested_query": safety_result["suggested_query"],
                        "data": [],
                        "error": False,  # Technically not a system error, just a guard block
                        "metadata": {}
                    }
                    processing_result = {"data": []}
                    visualization = {}
                else:
                    # Append safety result to thinking context so processing/SQL agents can use it
                    thinking_result["safety_guard"] = safety_result
                    
                    # Process with allowed agents only
                    from backend.ai_agent.agents.processing_agent import ProcessingAgent
                    processing_agent = ProcessingAgent()
                    processing_result = await processing_agent.execute(
                        query=query,
                        thinking_result=thinking_result,
                        allowed_agents=access_validation["allowed_agents"]
                    )
                    
                    # ── 3. Generate visualization and memory context for ALL requests ──
                    viz_agent = VisualizationAgent()
                    visualization = await viz_agent.generate(
                        query=query,
                        data=processing_result.get("data", []),
                        tool_used=processing_result.get("tool_used", "sql")
                    )
                    
                    # Build memory context via MemoryManager
                    memory_ctx = {}
                    if conversation_id:
                        try:
                            from backend.ai_agent.memory_manager import get_memory_manager
                            memory = get_memory_manager()
                            memory_ctx = memory.build_memory_context(
                                query=query,
                                session_id=conversation_id,
                                user_id=user_id,
                            )
                        except Exception as e:
                            logger.warning(f"MemoryManager unavailable, falling back: {e}")
                            memory_ctx = {
                                "conversation_history": self.get_session_messages(user_id, conversation_id),
                                "session_summary": "",
                                "cross_session_context": "",
                                "user_preferences": "",
                            }
                    
                    # Coordinate final response
                    from backend.ai_agent.agents.coordinator_agent import CoordinatorAgent
                    coordinator = CoordinatorAgent()
                    final_response = await coordinator.format_response(
                        query=query,
                        thinking_result=thinking_result,
                        processing_result=processing_result,
                        visualization=visualization,
                        memory_context=memory_ctx
                    )
            
            # Enrich response for storage and return
            # Strip internal metadata keys (starting with _) from rows before sending to frontend
            clean_data = []
            for row in processing_result.get("data", []):
                clean_row = {k: v for k, v in row.items() if not k.startswith("_")}
                clean_data.append(clean_row)
            
            final_response["data"] = clean_data
            final_response["chart_data"] = visualization.get("chart_data")
            final_response["agents_used"] = access_validation["allowed_agents"]
            final_response["agents_blocked"] = access_validation.get("blocked_agents", [])
            
            # Calculate timing
            end_time = datetime.now()
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # Add metadata to response
            final_response["metadata"] = final_response.get("metadata", {})
            final_response["metadata"].update({
                "user_id": user_id,
                "conversation_id": conversation_id,
                "duration_ms": duration_ms,
                "timestamp": datetime.now().isoformat()
            })

            # Determine fallback query for empty shortcut submissions
            stored_query = query if query and query.strip() else (report_name or "Report Query")

            # Store in conversation history and get ID
            message_id = self._store_conversation(user_id, conversation_id, stored_query, final_response)
            if message_id:
                final_response["metadata"]["message_id"] = message_id

            # ── Trigger post-response memory update (summarization etc.) ──
            if conversation_id:
                try:
                    from backend.ai_agent.memory_manager import get_memory_manager
                    memory = get_memory_manager()
                    memory.trigger_memory_update(
                        query=stored_query,
                        response_text=final_response.get("answer", ""),
                        session_id=conversation_id,
                        user_id=user_id,
                    )
                except Exception as e:
                    logger.warning(f"Memory update failed (non-critical): {e}")

            return final_response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"An error occurred: {str(e)}",
                "error": True,
                "metadata": {"user_id": user_id}
            }
    
    def _store_conversation(
        self,
        user_id: int,
        conversation_id: Optional[str],
        query: str,
        response: Dict[str, Any]
    ):
        """Store conversation in memory and data adapter"""
        if user_id not in self._conversation_history:
            self._conversation_history[user_id] = []
        
        import uuid
        message_id = str(uuid.uuid4())
        
        conversation_entry = {
            "conversation_id": conversation_id,
            "message_id": message_id,
            "query": query,
            "answer": response.get("answer", ""),
            "timestamp": datetime.now().isoformat()
        }
        
        self._conversation_history[user_id].append(conversation_entry)
        
        # Also persist to data adapter
        try:
            self.adapter.insert("conversations", {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "query": query,
                "response": response.get("answer", ""),
                "agents_used": response.get("agents_used", []),
                "timestamp": datetime.now().isoformat(),
                "data": response.get("data", []),
                "chart_data": response.get("chart_data"),
                "insights": response.get("insights", []),
                "recommendations": response.get("recommendations", []),
            })
            
            return message_id

        except Exception as e:
            logger.warning(f"Failed to persist conversation: {e}")
            return None
            from backend.ai_agent.db_logger import get_postgres_logger
            pg_logger = get_postgres_logger()
            pg_logger.log_conversation(
                user_id=user_id,
                conversation_id=conversation_id,
                query=query,
                response=response.get("answer", ""),
                agents_used=response.get("agents_used", []),
                metadata=response.get("metadata", {})
            )
            
        except Exception as e:
            logger.warning(f"Failed to persist conversation: {e}")
    
    def get_conversation_history(
        self,
        user_id: int,
        conversation_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a user"""
        filters = {"user_id": user_id}
        if conversation_id:
            filters["conversation_id"] = conversation_id
        
        conversations = self.adapter.query("conversations", filters)
        
        # Sort by timestamp descending and limit
        sorted_convos = sorted(
            conversations,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
        
        return sorted_convos
    
    def get_agent_state(self, user_id: int) -> Dict[str, Any]:
        """Get the current state of AI agents for a user"""
        all_agents = self.auth_service.get_all_domain_agents()
        user_agents = [a.get("code", "") for a in all_agents]
        
        return {
            "assigned_agents": user_agents,
            "all_agents": all_agents,
            "active_conversations": len(self._conversation_history.get(user_id, [])),
            "last_query_time": self._get_last_query_time(user_id)
        }
    
    def _get_last_query_time(self, user_id: int) -> Optional[str]:
        """Get the last query timestamp for a user"""
        history = self._conversation_history.get(user_id, [])
        if history:
            return history[-1].get("timestamp")
        return None
    
    def clear_memory(self, user_id: int, conversation_id: Optional[str] = None) -> bool:
        """Clear conversation memory for a user"""
        if conversation_id:
            # Clear specific conversation
            if user_id in self._conversation_history:
                self._conversation_history[user_id] = [
                    c for c in self._conversation_history[user_id]
                    if c.get("conversation_id") != conversation_id
                ]
        else:
            # Clear all conversations for user
            self._conversation_history[user_id] = []
        
        return True
    
    def get_sessions(
        self,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get a list of conversation sessions for a user"""
        conversations = self.adapter.query("conversations", {"user_id": user_id})
        
        # Group by conversation_id
        sessions: Dict[str, Dict[str, Any]] = {}
        for conv in conversations:
            session_id = conv.get("conversation_id")
            title = conv.get("query", "Conversation")[:50]
            
            # If no conversation_id exists (legacy message), group them all together
            if not session_id:
                session_id = "legacy_chat"
                title = "Legacy Chat History"
            
            if str(session_id) not in sessions:
                sessions[str(session_id)] = {
                    "session_id": str(session_id),
                    "title": title,
                    "query": conv.get("query", ""),
                    "message_count": 0,
                    "first_message": conv.get("timestamp"),
                    "last_message": conv.get("timestamp"),
                }
            
            sessions[session_id]["message_count"] += 1
            
            # Update last message timestamp
            if conv.get("timestamp", "") > sessions[session_id]["last_message"]:
                sessions[session_id]["last_message"] = conv.get("timestamp")
        
        # Sort by last_message descending
        sorted_sessions = sorted(
            sessions.values(),
            key=lambda x: x.get("last_message", ""),
            reverse=True
        )
        
        # Apply pagination
        return sorted_sessions[offset:offset + limit]
    
    def get_session_messages(
        self,
        user_id: int,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get all messages for a specific session"""
        
        # If accessing the grouped legacy chat, fetch all where conversation_id is NULL
        if session_id == "legacy_chat":
            conversations = self.adapter.query(
                "conversations", 
                {"user_id": user_id, "conversation_id": None}
            )
        else:
            conversations = self.adapter.query(
                "conversations", 
                {"user_id": user_id, "conversation_id": str(session_id)}
            )
            
            # Fallback for old messages that didn't have conversation_id and were grouped by id
            if not conversations and str(session_id).isdigit():
                conversations = self.adapter.query(
                    "conversations",
                    {"user_id": user_id, "id": int(session_id)}
                )
                
        # Create messages list with alternating user/assistant format
        messages = []
        for conv in sorted(conversations, key=lambda x: x.get("timestamp", "")):
            # Add user message
            messages.append({
                "role": "user",
                "content": conv.get("query", ""),
                "query": conv.get("query", ""),
                "timestamp": conv.get("timestamp"),
            })
            # Add assistant message
            messages.append({
                "role": "assistant",
                "content": conv.get("response", ""),
                "query": conv.get("query", ""),
                "timestamp": conv.get("timestamp"),
                "agents_used": conv.get("agents_used", []),
                "chart_data": conv.get("chart_data"),
                "data": conv.get("data", []),
                "insights": conv.get("insights", []),
                "recommendations": conv.get("recommendations", []),
                "metadata": conv.get("metadata", {}),
                "feedback": conv.get("feedback"),
                "message_id": conv.get("message_id"),
            })
        
        return messages
    
    def delete_session(self, user_id: int, session_id: str) -> bool:
        """Delete a conversation session"""
        try:
            # Remove from memory
            if user_id in self._conversation_history:
                self._conversation_history[user_id] = [
                    c for c in self._conversation_history[user_id]
                    if c.get("conversation_id") != session_id
                ]
            
            # Remove from adapter (if supported)
            try:
                conversations = self.adapter.query(
                    "conversations", 
                    {"user_id": user_id, "conversation_id": session_id}
                )
                for conv in conversations:
                    self.adapter.delete("conversations", conv.get("id"))
            except Exception as e:
                logger.warning(f"Could not delete from adapter: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    def submit_feedback(
        self,
        user_id: int,
        message_id: str,
        rating: str,  # "positive" or "negative"
        comment: Optional[str] = None
    ) -> bool:
        """Submit feedback for a specific AI response and trigger preference learning"""
        try:
            # Persist to existing feedback table
            self.adapter.insert("feedback", {
                "user_id": user_id,
                "message_id": message_id,
                "rating": rating,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            })
            
            # Update the feedback column directly on conversations
            try:
                from sqlalchemy import text
                from backend.ai_agent.database_service import get_engine
                engine = get_engine()
                if engine:
                    with engine.connect() as conn:
                        conn.execute(
                            text("UPDATE conversations SET feedback = :rating WHERE message_id = :msg_id OR (message_id IS NULL AND conversation_id = :msg_id)"),
                            {"rating": rating, "msg_id": message_id}
                        )
                        conn.commit()
            except Exception as e:
                logger.warning(f"Failed to update conversation feedback field: {e}")
                
            logger.info(f"Feedback stored for message {message_id}: {rating}")

            # ── Trigger preference learning from feedback ──
            try:
                # Find the original query/response for this message
                query_text = ""
                response_text = ""
                convs = self.adapter.query("conversations", {"conversation_id": message_id})
                if convs:
                    query_text = convs[0].get("query", "")
                    response_text = convs[0].get("response", "")

                from backend.ai_agent.memory_manager import get_memory_manager
                memory = get_memory_manager()
                memory.extract_preferences_from_feedback(
                    user_id=user_id,
                    rating=rating,
                    query=query_text,
                    response=response_text,
                    comment=comment,
                )
            except Exception as e:
                logger.warning(f"Preference learning from feedback failed: {e}")

            return True

        except Exception as e:
            logger.error(f"Error submitting feedback: {e}")
            return False


# Global singleton
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create the AI service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
