"""
Token Counter - Lightweight token estimation for memory management.
Uses word-count heuristics (no heavy tokenizer dependencies).
Accurate enough for budget enforcement with Gemma3 / Ollama models.
"""
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Average ratio: 1 word ≈ 1.3 tokens for English/Arabic mix
_WORD_TO_TOKEN_RATIO = 1.3


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a text string.
    Uses word-count × 1.3 heuristic.
    """
    if not text:
        return 0
    words = len(text.split())
    return int(words * _WORD_TO_TOKEN_RATIO)


def estimate_messages_tokens(messages: List[Dict]) -> int:
    """
    Estimate total tokens for a list of chat messages.
    Each message adds ~4 tokens overhead for role/formatting.
    """
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        total += estimate_tokens(content) + 4  # role + formatting overhead
    return total


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """
    Truncate text to fit within max_tokens, breaking at sentence boundaries.
    Prefers keeping complete sentences over cutting mid-sentence.
    """
    if not text:
        return ""

    current_tokens = estimate_tokens(text)
    if current_tokens <= max_tokens:
        return text

    # Split into sentences (handles English and Arabic)
    sentences = re.split(r'(?<=[.!?؟。\n])\s+', text)

    result = []
    used_tokens = 0
    for sentence in sentences:
        sentence_tokens = estimate_tokens(sentence)
        if used_tokens + sentence_tokens > max_tokens:
            break
        result.append(sentence)
        used_tokens += sentence_tokens

    # If no complete sentence fits, do a word-level truncation
    if not result:
        words = text.split()
        target_words = int(max_tokens / _WORD_TO_TOKEN_RATIO)
        return " ".join(words[:target_words]) + "..."

    return " ".join(result)


def truncate_messages_to_budget(
    messages: List[Dict],
    max_tokens: int
) -> List[Dict]:
    """
    Trim a list of messages (oldest first) to fit within token budget.
    Keeps the most recent messages that fit.
    Returns a new list (does not mutate input).
    """
    if not messages:
        return []

    # Work backwards from most recent
    result = []
    used_tokens = 0
    for msg in reversed(messages):
        msg_tokens = estimate_tokens(msg.get("content", "")) + 4
        if used_tokens + msg_tokens > max_tokens:
            break
        result.insert(0, msg)
        used_tokens += msg_tokens

    logger.debug(f"[MEMORY] Trimmed {len(messages)} messages to {len(result)}, {used_tokens}/{max_tokens} tokens")
    return result
