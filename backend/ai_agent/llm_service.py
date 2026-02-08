import logging
import json
from typing import Dict, Any, List, Optional
import ollama

from backend.config import AI_CONFIG
from backend.ai_agent.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with LLM providers (Ollama)"""
    
    def __init__(self):
        self.provider = AI_CONFIG.get("model_provider", "ollama")
        self.base_url = AI_CONFIG.get("ollama_base_url", "http://localhost:11434")
        self.model = AI_CONFIG.get("ollama_model", "gemma3:latest")
        self.options = AI_CONFIG.get("ollama_options", {})
        self.prompt_manager = get_prompt_manager()
        
        # Configure client
        # Note: ollama python client uses generic env vars or defaults, 
        # but we can try to set it if needed. 
        # For now assuming local default or config.
        
    async def generate_response(
        self, 
        query: str, 
        data: List[Dict], 
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a natural language response based on data and query
        """
        try:
            # 1. Get System Prompt
            system_prompt = self.prompt_manager.get_system_prompt()
            
            # 2. Format Data Context
            data_summary = self._format_data_for_llm(data)
            
            # 3. Build User Message
            current_user_message = f"""
Query: "{query}"

Analysis Context:
- Domain: {context.get('allowed_domains', [])}
- Tool Used: {context.get('tool_used', 'unknown')}
- Query Type: {context.get('query_type', 'general')}

Data Results:
{data_summary}

Based on this data, provide a response following the defined communication style.
"""

            # 4. Construct Messages
            messages = [{'role': 'system', 'content': system_prompt}]
            
            # Add history (limit to last 4 messages for faster context processing)
            history = context.get('history', [])
            if history:
                # Filter to only valid roles and content
                clean_history = []
                for msg in history[-4:]:  # Reduced from 10 to 4 for speed
                    role = msg.get('role')
                    content = msg.get('content')
                    if role in ['user', 'assistant'] and content:
                        # Truncate long messages in history
                        truncated_content = str(content)[:500] if len(str(content)) > 500 else str(content)
                        clean_history.append({'role': role, 'content': truncated_content})
                messages.extend(clean_history)
            
            # Add current message
            messages.append({'role': 'user', 'content': current_user_message})

            # 5. Call LLM
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
                duration_ns = response['eval_duration'] # Nanoseconds
                duration_sec = duration_ns / 1_000_000_000
                speed = tokens / duration_sec if duration_sec > 0 else 0
                logger.info(f"[LLM STATS] Generated {tokens} tokens in {duration_sec:.2f}s ({speed:.2f} t/s)")
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"[LLM SERVICE] Error generating response: {e}")
            return self._fallback_response(query, data)

    def _format_data_for_llm(self, data: List[Dict]) -> str:
        """Format data list into a string for the LLM"""
        if not data:
            return "No data found matching the query."
            
        # Limit data to avoid context overflow (reduced for speed)
        max_items = 10
        total_count = len(data)
        truncated = False
        
        display_data = data
        if total_count > max_items:
            display_data = data[:max_items]
            truncated = True
            
        # Convert to compact JSON string (no indent for speed, ensure_ascii=False for Arabic)
        data_str = json.dumps(display_data, default=str, ensure_ascii=False)
        
        if truncated:
            data_str += f"\n\n[Note: Showing {max_items} of {total_count} records. Use SQL count for precise large numbers.]"
            
        return data_str

    def _fallback_response(self, query: str, data: List[Dict]) -> str:
        """Simple fallback if LLM fails"""
        return f"Found {len(data)} results for '{query}'. (AI processing unavailable)"

# Singleton
_llm_service = None

def get_llm_service():
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
