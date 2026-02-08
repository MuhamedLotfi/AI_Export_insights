"""
Domain Agents API Router
Manages domain agent access and assignments
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.routers.auth import get_current_user

router = APIRouter()


class DomainAgentResponse(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    capabilities: List[str] = []


class AgentAssignment(BaseModel):
    user_id: int
    agent_code: str


class BulkAgentAssignment(BaseModel):
    user_id: int
    agent_codes: List[str]


class UserAgentsResponse(BaseModel):
    user_id: int
    username: str
    assigned_agents: List[str]


@router.get("/", response_model=List[DomainAgentResponse])
async def get_all_agents(current_user: dict = Depends(get_current_user)):
    """
    Get all available domain agents
    """
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    agents = auth_service.get_all_domain_agents()
    
    return [
        DomainAgentResponse(
            code=a.get("code", ""),
            name=a.get("name", ""),
            description=a.get("description", ""),
            icon=a.get("icon", "smart_toy"),
            capabilities=a.get("capabilities", [])
        )
        for a in agents
    ]


@router.get("/my", response_model=List[str])
async def get_my_agents(current_user: dict = Depends(get_current_user)):
    """
    Get agents assigned to the current user
    """
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    return auth_service.get_user_domain_agents(current_user["id"])


@router.get("/user/{user_id}", response_model=UserAgentsResponse)
async def get_user_agents(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get agents assigned to a specific user (admin or self)
    """
    if current_user.get("role") != "admin" and current_user["id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to view this user's agents"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    user = auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    agents = auth_service.get_user_domain_agents(user_id)
    
    return UserAgentsResponse(
        user_id=user_id,
        username=user.get("username", ""),
        assigned_agents=agents
    )


@router.post("/assign")
async def assign_agent(
    assignment: AgentAssignment,
    current_user: dict = Depends(get_current_user)
):
    """
    Assign a domain agent to a user (admin only)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    
    # Verify user exists
    user = auth_service.get_user_by_id(assignment.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Verify agent exists
    all_agents = auth_service.get_all_domain_agents()
    agent_codes = [a.get("code") for a in all_agents]
    
    if assignment.agent_code not in agent_codes:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent code: {assignment.agent_code}"
        )
    
    success = auth_service.assign_domain_agent(
        user_id=assignment.user_id,
        agent_code=assignment.agent_code,
        granted_by=current_user["id"]
    )
    
    if success:
        return {"message": f"Agent '{assignment.agent_code}' assigned to user {assignment.user_id}"}
    
    raise HTTPException(
        status_code=500,
        detail="Failed to assign agent"
    )


@router.delete("/revoke")
async def revoke_agent(
    assignment: AgentAssignment,
    current_user: dict = Depends(get_current_user)
):
    """
    Revoke a domain agent from a user (admin only)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    
    success = auth_service.revoke_domain_agent(
        user_id=assignment.user_id,
        agent_code=assignment.agent_code
    )
    
    if success:
        return {"message": f"Agent '{assignment.agent_code}' revoked from user {assignment.user_id}"}
    
    return {"message": "Agent was not assigned to user"}


@router.put("/user/{user_id}")
async def update_user_agents(
    user_id: int,
    assignment: BulkAgentAssignment,
    current_user: dict = Depends(get_current_user)
):
    """
    Bulk update agents for a user (admin only)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    
    # Verify user exists
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    success = auth_service.update_user_domain_agents(
        user_id=user_id,
        agent_codes=assignment.agent_codes,
        granted_by=current_user["id"]
    )
    
    if success:
        return {
            "message": f"User agents updated",
            "user_id": user_id,
            "agents": assignment.agent_codes
        }
    
    raise HTTPException(
        status_code=500,
        detail="Failed to update user agents"
    )


@router.get("/users-with-agents")
async def get_all_users_with_agents(current_user: dict = Depends(get_current_user)):
    """
    Get all users with their assigned agents (admin only)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    users = auth_service.get_all_users()
    
    result = []
    for user in users:
        agents = auth_service.get_user_domain_agents(user["id"])
        result.append({
            "user_id": user["id"],
            "username": user["username"],
            "email": user.get("email", ""),
            "role": user.get("role", "user"),
            "assigned_agents": agents
        })
    
    return {"users": result}


@router.post("/validate-access")
async def validate_agent_access(
    required_agents: List[str],
    current_user: dict = Depends(get_current_user)
):
    """
    Validate if current user has access to specified agents
    """
    from backend.ai_agent.auth_service import get_auth_service
    
    auth_service = get_auth_service()
    validation = auth_service.validate_agent_access(
        user_id=current_user["id"],
        required_agents=required_agents
    )
    
    return validation
