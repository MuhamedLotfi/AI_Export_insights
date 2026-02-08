"""
Router module exports
"""
from backend.routers.auth import router as auth_router
from backend.routers.ai import router as ai_router
from backend.routers.dashboard import router as dashboard_router
from backend.routers.settings import router as settings_router
from backend.routers.domain_agents import router as domain_agents_router

__all__ = [
    "auth_router",
    "ai_router",
    "dashboard_router",
    "settings_router",
    "domain_agents_router",
]
