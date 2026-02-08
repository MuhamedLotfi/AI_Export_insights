"""
Authentication Service
Handles user authentication, JWT tokens, and domain agent access
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext

from backend.config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
from backend.ai_agent.data_adapter import get_adapter

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and user management service"""
    
    def __init__(self):
        self.adapter = get_adapter()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user and return user data with token"""
        users = self.adapter.query("users", {"username": username})
        
        if not users:
            logger.warning(f"User not found: {username}")
            return None
        
        user = users[0]
        
        if not self.verify_password(password, user.get("password_hash", "")):
            logger.warning(f"Invalid password for user: {username}")
            return None
        
        # Get user's domain agents
        user_agents = self.get_user_domain_agents(user["id"])
        
        # Create token
        token_data = {
            "sub": str(user["id"]),
            "username": user["username"],
            "role": user.get("role", "user"),
            "agents": user_agents
        }
        token = self.create_access_token(token_data)
        
        # Return user info (without password)
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user.get("email", ""),
            "role": user.get("role", "user"),
            "domain_agents": user_agents,
            "access_token": token,
            "token_type": "bearer"
        }
    
    def register_user(self, username: str, email: str, password: str, role: str = "user") -> Optional[Dict[str, Any]]:
        """Register a new user"""
        # Check if username exists
        existing = self.adapter.query("users", {"username": username})
        if existing:
            return None
        
        # Create user
        user_data = {
            "username": username,
            "email": email,
            "password_hash": self.hash_password(password),
            "role": role,
            "is_active": True,
            "created_at": datetime.now().isoformat()
        }
        
        user = self.adapter.insert("users", user_data)
        logger.info(f"User registered: {username}")
        
        # Return without password
        del user["password_hash"]
        return user
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user = self.adapter.get_by_id("users", user_id)
        if user:
            user = dict(user)
            user.pop("password_hash", None)
        return user
    
    def get_user_from_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user data from JWT token"""
        payload = self.decode_token(token)
        if not payload:
            return None
        
        user_id = int(payload.get("sub", 0))
        return self.get_user_by_id(user_id)
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all users (admin only)"""
        users = self.adapter.get_all("users")
        # Remove password hashes
        return [{k: v for k, v in u.items() if k != "password_hash"} for u in users]
    
    def update_user(self, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update user data"""
        # Don't allow password update through this method
        data.pop("password_hash", None)
        data.pop("password", None)
        
        return self.adapter.update("users", user_id, data)
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user"""
        return self.adapter.delete("users", user_id)
    
    def reset_password(self, user_id: int, new_password: str) -> bool:
        """Reset a user's password"""
        password_hash = self.hash_password(new_password)
        result = self.adapter.update("users", user_id, {"password_hash": password_hash})
        return bool(result)

    # Domain Agent Access Methods
    
    def get_user_domain_agents(self, user_id: int) -> List[str]:
        """Get domain agents assigned to a user"""
        assignments = self.adapter.query("user_agents", {"user_id": user_id})
        return [a.get("agent_code") for a in assignments if a.get("is_active", True)]
    
    def assign_domain_agent(self, user_id: int, agent_code: str, granted_by: Optional[int] = None) -> bool:
        """Assign a domain agent to a user"""
        # Check if already assigned
        existing = self.adapter.query("user_agents", {"user_id": user_id, "agent_code": agent_code})
        if existing:
            return True
        
        self.adapter.insert("user_agents", {
            "user_id": user_id,
            "agent_code": agent_code,
            "is_active": True,
            "granted_by": granted_by,
            "granted_at": datetime.now().isoformat()
        })
        logger.info(f"Assigned agent {agent_code} to user {user_id}")
        return True
    
    def revoke_domain_agent(self, user_id: int, agent_code: str) -> bool:
        """Revoke a domain agent from a user"""
        assignments = self.adapter.query("user_agents", {"user_id": user_id, "agent_code": agent_code})
        if assignments:
            return self.adapter.delete("user_agents", assignments[0].get("id"))
        return False
    
    def update_user_domain_agents(self, user_id: int, agent_codes: List[str], granted_by: Optional[int] = None) -> bool:
        """Update user's domain agents (bulk)"""
        # Get current assignments
        current = self.get_user_domain_agents(user_id)
        
        # Remove agents not in new list
        for agent in current:
            if agent not in agent_codes:
                self.revoke_domain_agent(user_id, agent)
        
        # Add new agents
        for agent in agent_codes:
            if agent not in current:
                self.assign_domain_agent(user_id, agent, granted_by)
        
        return True
    
    def get_all_domain_agents(self) -> List[Dict[str, Any]]:
        """Get all available domain agents"""
        agents = self.adapter.get_all("agents")
        
        # Ensure we have the agents defined in config
        from backend.config import DOMAIN_AGENTS
        
        # Create a set of existing codes
        existing_codes = {a.get("code") for a in agents}
        
        # Add any missing agents from config
        for code, info in DOMAIN_AGENTS.items():
            if code not in existing_codes:
                agents.append({
                    "code": code,
                    "name": info["name"],
                    "description": info["description"],
                    "icon": info["icon"],
                    "capabilities": info.get("keywords", []),
                    "is_active": True
                })
                
        return agents
    
    def validate_agent_access(self, user_id: int, required_agents: List[str]) -> Dict[str, Any]:
        """Validate if user has access to required agents"""
        user_agents = self.get_user_domain_agents(user_id)
        
        allowed = [a for a in required_agents if a in user_agents]
        blocked = [a for a in required_agents if a not in user_agents]
        
        return {
            "allowed_agents": allowed,
            "blocked_agents": blocked,
            "has_access": len(blocked) == 0,
            "partial_access": len(allowed) > 0 and len(blocked) > 0
        }


# Global singleton
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create the auth service singleton"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
