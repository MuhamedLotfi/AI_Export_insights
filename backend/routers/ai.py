"""
AI Agent API Router
Handles chat, query processing, and conversation management
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.routers.auth import get_current_user

router = APIRouter()


# Pydantic Models
class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    thinking_trace: Optional[Dict[str, Any]] = None
    data: List[Dict[str, Any]] = []
    chart_data: Optional[Dict[str, Any]] = None
    insights: List[Dict[str, Any]] = []
    recommendations: List[Dict[str, Any]] = []
    agents_used: List[str] = []
    agents_blocked: List[str] = []
    metadata: Dict[str, Any] = {}
    error: Optional[bool] = False


class ConversationResponse(BaseModel):
    id: Optional[str] = None
    query: str
    response: str
    timestamp: str
    agents_used: List[str] = []


class AgentStateResponse(BaseModel):
    assigned_agents: List[str]
    all_agents: List[Dict[str, Any]]
    active_conversations: int
    last_query_time: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Process a user query through the AI agent pipeline
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    result = await ai_service.process_query(
        query=request.query,
        user_id=current_user["id"],
        conversation_id=request.conversation_id
    )
    
    return ChatResponse(**result)


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    conversation_id: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Get conversation history for the current user
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    conversations = ai_service.get_conversation_history(
        user_id=current_user["id"],
        conversation_id=conversation_id,
        limit=limit
    )
    
    return [
        ConversationResponse(
            id=c.get("conversation_id"),
            query=c.get("query", ""),
            response=c.get("response", ""),
            timestamp=c.get("timestamp", ""),
            agents_used=c.get("agents_used", [])
        )
        for c in conversations
    ]


@router.get("/state", response_model=AgentStateResponse)
async def get_agent_state(current_user: dict = Depends(get_current_user)):
    """
    Get the current state of AI agents for the user
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    state = ai_service.get_agent_state(current_user["id"])
    
    return AgentStateResponse(**state)


@router.delete("/memory")
async def clear_memory(
    conversation_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Clear conversation memory for the user
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    success = ai_service.clear_memory(
        user_id=current_user["id"],
        conversation_id=conversation_id
    )
    
    if conversation_id:
        return {"message": f"Memory cleared for conversation {conversation_id}"}
    return {"message": "All memory cleared"}


@router.get("/schema")
async def get_data_schema(current_user: dict = Depends(get_current_user)):
    """
    Get the data schema (available tables and columns)
    """
    from backend.ai_agent.data_adapter import get_adapter
    
    adapter = get_adapter()
    schema = adapter.get_schema()
    
    return {
        "tables": schema,
        "table_count": len(schema)
    }


@router.post("/query-raw")
async def execute_raw_query(
    query: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Execute a raw SQL-like query (admin only)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from backend.ai_agent.data_adapter import get_adapter
    
    adapter = get_adapter()
    
    try:
        results = adapter.execute_query(query)
        return {
            "data": results,
            "row_count": len(results)
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Query error: {str(e)}"
        )


# ===== SESSION-BASED CONVERSATION HISTORY =====

class SessionResponse(BaseModel):
    session_id: str
    title: str
    query: Optional[str] = None
    message_count: int = 0
    first_message: Optional[str] = None
    last_message: Optional[str] = None


class SessionMessagesResponse(BaseModel):
    status: str = "success"
    session_id: str
    messages: List[Dict[str, Any]] = []


@router.get("/conversations/sessions")
async def get_sessions(
    limit: int = 10,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a list of conversation sessions for the current user
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    sessions = ai_service.get_sessions(
        user_id=current_user["id"],
        limit=limit,
        offset=offset
    )
    
    return {
        "status": "success",
        "sessions": sessions
    }


@router.get("/conversations/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all messages for a specific conversation session
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    messages = ai_service.get_session_messages(
        user_id=current_user["id"],
        session_id=session_id
    )
    
    return {
        "status": "success",
        "session_id": session_id,
        "messages": messages
    }


@router.delete("/conversations/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a conversation session
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    success = ai_service.delete_session(
        user_id=current_user["id"],
        session_id=session_id
    )
    
    if success:
        return {"status": "success", "message": f"Session {session_id} deleted"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete session"
        )


class FeedbackRequest(BaseModel):
    message_id: str
    rating: str  # "positive" or "negative"
    comment: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Submit feedback for an AI response
    """
    from backend.ai_agent.ai_service import get_ai_service
    
    ai_service = get_ai_service()
    
    success = ai_service.submit_feedback(
        user_id=current_user["id"],
        message_id=request.message_id,
        rating=request.rating,
        comment=request.comment
    )
    
    if success:
        return {"status": "success", "message": "Feedback submitted"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to submit feedback"
        )
