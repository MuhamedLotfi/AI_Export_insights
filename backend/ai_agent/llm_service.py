"""
LLM Service - Natural Language Generation
Integrates with Ollama (Gemma3) for response generation with native Arabic support
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional
import ollama

from backend.config import AI_CONFIG
from backend.ai_agent.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with LLM providers (Ollama) with native Arabic support"""
    
    # Arabic Unicode range pattern for language detection
    ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]')
    
    def __init__(self):
        self.provider = AI_CONFIG.get("model_provider", "ollama")
        self.base_url = AI_CONFIG.get("ollama_base_url", "http://localhost:11434")
        self.model = AI_CONFIG.get("ollama_model")
        self.options = AI_CONFIG.get("ollama_options", {})
        self.output_language = AI_CONFIG.get("output_language", "ar")
        self.prompt_manager = get_prompt_manager()
        
        logger.info(f"LLMService initialized with model: {self.model}, output_language: {self.output_language}")
        
    async def generate_response(
        self, 
        query: str, 
        data: List[Dict], 
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a natural language response based on data and query.
        The multilingual model handles Arabic natively.
        """
        try:
            # 1. Detect language for response formatting
            original_language = self._detect_language(query)
            working_query = query
            
            # 2. Get System Prompt
            system_prompt = self.prompt_manager.get_system_prompt()
            
            # 3. Format Data Context
            data_summary = self._format_data_for_llm(data)
            
            # 4. Build User Message
            language_instruction = "CRITICAL: You MUST write your final response entirely in Arabic." if self.output_language == "ar" or original_language == "ar" else ""
            
            current_user_message = f"""
Query: "{working_query}"

Analysis Context:
- Domain: {context.get('allowed_domains', [])}
- Tool Used: {context.get('tool_used', 'unknown')}
- Query Type: {context.get('query_type', 'general')}

Data Results:
{data_summary}

Based on this data, provide a response following the defined communication style.
{language_instruction}
"""

            # 5. Construct Messages — memory-aware context building
            # Order: system prompt → preferences (stable) → summary → cross-session → history → current query
            messages = [{'role': 'system', 'content': system_prompt}]

            # Inject user preferences (most stable, helps KV cache)
            user_prefs = context.get('user_preferences', '')
            if user_prefs:
                messages.append({
                    'role': 'system',
                    'content': f'User preferences:\n{user_prefs}'
                })

            # Inject session summary
            session_summary = context.get('session_summary', '')
            if session_summary:
                messages.append({
                    'role': 'system',
                    'content': f'Conversation summary so far:\n{session_summary}'
                })

            # Inject cross-session context
            cross_session = context.get('cross_session_context', '')
            if cross_session:
                messages.append({
                    'role': 'system',
                    'content': f'Relevant context from past conversations:\n{cross_session}'
                })

            # Add conversation history (already token-budgeted by MemoryManager)
            history = context.get('conversation_history', context.get('history', []))
            if history:
                clean_history = []
                for msg in history:
                    role = msg.get('role')
                    content = msg.get('content')
                    if role in ['user', 'assistant'] and content:
                        clean_history.append({'role': role, 'content': str(content)})
                messages.extend(clean_history)

            
            # Add current message
            messages.append({'role': 'user', 'content': current_user_message})

            # 6. Call LLM (Gemma3)
            logger.info(f"[LLM SERVICE] Calling {self.model} with {len(messages)} messages")
            
            # keep_alive keeps model in memory for faster subsequent calls
            response = ollama.chat(
                model=self.model, 
                messages=messages, 
                options=self.options,
                keep_alive="10m"  # Keep model loaded for 10 minutes
            )
            
            # Log metrics
            if 'eval_count' in response and 'eval_duration' in response:
                tokens = response['eval_count']
                duration_ns = response['eval_duration']  # Nanoseconds
                duration_sec = duration_ns / 1_000_000_000
                speed = tokens / duration_sec if duration_sec > 0 else 0
                logger.info(f"[LLM STATS] Generated {tokens} tokens in {duration_sec:.2f}s ({speed:.2f} t/s)")
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"[LLM SERVICE] Error generating response: {e}")
            import traceback
            traceback.print_exc()
            return self._fallback_response(query, data, original_language if 'original_language' in dir() else "en")

    def _detect_language(self, text: str) -> str:
        """Detect if text is primarily Arabic or English. Returns 'ar' or 'en'."""
        if not text:
            return "en"
        arabic_char_count = sum(1 for c in text if self.ARABIC_PATTERN.match(c))
        total_alpha = sum(1 for c in text if c.isalpha())
        if total_alpha == 0:
            return "en"
        arabic_ratio = arabic_char_count / total_alpha
        return "ar" if arabic_ratio > 0.3 else "en"

    def _format_data_for_llm(self, data: List[Dict]) -> str:
        """Format data list into a readable string for the LLM"""
        if not data:
            return "No data found matching the query."
            
        # Allow more items for nested/subtable data
        max_items = 30
        total_count = len(data)
        truncated = False
        
        display_data = data
        if total_count > max_items:
            display_data = data[:max_items]
            truncated = True
        
        # Check if this is subtable data (has _source_table or reference_type)
        is_subtable = any("_source_table" in item or "reference_type" in item for item in display_data if isinstance(item, dict))
        
        if is_subtable:
            # Format as structured summary for better LLM comprehension
            lines = []
            for i, item in enumerate(display_data, 1):
                parts = [f"Record {i}:"]
                for key, val in item.items():
                    if key.startswith("_"):
                        continue
                    if isinstance(val, (dict, list)):
                        continue
                    if val is not None and val != "" and val != "None":
                        # Format numbers with commas
                        if isinstance(val, (int, float)) and key in ("totals", "amount", "total"):
                            parts.append(f"  {key}: {val:,.0f}")
                        else:
                            parts.append(f"  {key}: {val}")
                lines.append("\n".join(parts))
            
            data_str = "\n\n".join(lines)
            
            # Add source context
            source = display_data[0].get("_source_table", "") if display_data else ""
            project = display_data[0].get("_project_name", "") if display_data else ""
            if source:
                data_str = f"Source: {source}\nProject: {project}\nTotal Records: {total_count}\n\n{data_str}"
        else:
            # Convert to compact JSON string (ensure_ascii=False for Arabic)
            data_str = json.dumps(display_data, default=str, ensure_ascii=False)
        
        if truncated:
            data_str += f"\n\n[Showing {max_items} of {total_count} records]"
            
        return data_str

    def _fallback_response(self, query: str, data: List[Dict], language: str = "en") -> str:
        """Simple fallback if LLM fails"""
        if language == "ar":
            return f"تم العثور على {len(data)} نتيجة لـ '{query}'. (معالجة الذكاء الاصطناعي غير متاحة)"
        return f"Found {len(data)} results for '{query}'. (AI processing unavailable)"


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create the LLM service singleton"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
