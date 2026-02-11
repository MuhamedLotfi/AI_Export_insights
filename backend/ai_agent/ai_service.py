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
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user query through the multi-agent pipeline
        """
        start_time = datetime.now()
        
        try:
            # Get user's allowed agents
            user_agents = self.auth_service.get_user_domain_agents(user_id)
            
            if not user_agents:
                return {
                    "answer": "You don't have access to any AI agents. Please contact an administrator.",
                    "error": True,
                    "metadata": {"user_id": user_id}
                }
            
            # Route query to determine required domains
            from backend.ai_agent.agents.thinking_agent import ThinkingAgent
            thinking_agent = ThinkingAgent()
            thinking_result = await thinking_agent.analyze(query, user_agents)
            
            # Validate access
            required_domains = thinking_result.get("required_domains", [])
            access_validation = self.auth_service.validate_agent_access(user_id, required_domains)
            
            if not access_validation["has_access"] and not access_validation["partial_access"]:
                return {
                    "answer": f"You don't have access to the required domains: {access_validation['blocked_agents']}",
                    "error": True,
                    "blocked_agents": access_validation["blocked_agents"],
                    "metadata": {"user_id": user_id}
                }
            
            # Process with allowed agents only
            from backend.ai_agent.agents.processing_agent import ProcessingAgent
            processing_agent = ProcessingAgent()
            processing_result = await processing_agent.execute(
                query=query,
                thinking_result=thinking_result,
                allowed_agents=access_validation["allowed_agents"]
            )
            
            # Generate visualization if applicable
            from backend.ai_agent.agents.visualization_agent import VisualizationAgent
            viz_agent = VisualizationAgent()
            visualization = await viz_agent.generate(
                query=query,
                data=processing_result.get("data", [])
            )
            
            # Get history for context
            history = []
            if conversation_id:
                history = self.get_session_messages(user_id, conversation_id)

            # Coordinate final response
            from backend.ai_agent.agents.coordinator_agent import CoordinatorAgent
            coordinator = CoordinatorAgent()
            final_response = await coordinator.format_response(
                query=query,
                thinking_result=thinking_result,
                processing_result=processing_result,
                visualization=visualization,
                history=history
            )
            
            # Enrich response for storage and return
            final_response["data"] = processing_result.get("data", [])
            final_response["chart_data"] = visualization.get("chart_data")
            final_response["agents_used"] = access_validation["allowed_agents"]
            final_response["agents_blocked"] = access_validation.get("blocked_agents", [])
            
                "timestamp": datetime.now().isoformat()
            })

            # Store in conversation history and get ID
            message_id = self._store_conversation(user_id, conversation_id, query, final_response)
            if message_id:
                final_response["metadata"]["message_id"] = message_id
            
            return final_response
            
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
        
        conversation_entry = {
            "conversation_id": conversation_id,
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
                "query": query,
                "response": response.get("answer", ""),
                "agents_used": response.get("agents_used", []),
                "timestamp": datetime.now().isoformat(),
                "data": response.get("data", []),
                "chart_data": response.get("chart_data"),
                "insights": response.get("insights", []),
                "recommendations": response.get("recommendations", []),
            })
            
            # Return the ID (or generate one if using DB logic above is async/complex)
            message_id = conversation_id if conversation_id else f"msg_{datetime.now().timestamp()}"
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
        user_agents = self.auth_service.get_user_domain_agents(user_id)
        all_agents = self.auth_service.get_all_domain_agents()
        
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
            session_id = conv.get("conversation_id") or conv.get("id")
            if not session_id:
                continue
            
            if session_id not in sessions:
                sessions[session_id] = {
                    "session_id": session_id,
                    "title": conv.get("query", "Conversation")[:50],
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
        conversations = self.adapter.query(
            "conversations", 
            {"user_id": user_id, "conversation_id": session_id}
        )
        
        # Create messages list with alternating user/assistant format
        messages = []
        for conv in sorted(conversations, key=lambda x: x.get("timestamp", "")):
            # Add user message
            messages.append({
                "role": "user",
                "content": conv.get("query", ""),
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
                "metadata": conv.get("metadata"),
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
        rating: str, # "positive" or "negative"
        comment: Optional[str] = None
    ) -> bool:
        """Submit feedback for a specific AI response"""
        try:
            # Update in memory (if available)
            if user_id in self._conversation_history:
                for conv in self._conversation_history[user_id]:
                    # Simple matching - in real DB this would be by ID
                    # Since we don't have per-message IDs in memory structure easily w/o refactor,
                    # we'll skip memory update or do best-effort match if we had IDs there.
                    pass
            
            # Persist to data adapter
            try:
                # Store feedback as a new record or update existing conversation if ID schema matches
                # For now, let's store it in a 'feedback' table
                self.adapter.insert("feedback", {
                    "user_id": user_id,
                    "message_id": message_id,
                    "rating": rating,
                    "comment": comment,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"Feedback stored for message {message_id}: {rating}")
                return True
            except Exception as e:
                logger.warning(f"Could not store feedback: {e}")
                return False
                
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
