"""
Settings API Router
Manages application settings and configuration
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.routers.auth import get_current_user

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: Any


class SettingsResponse(BaseModel):
    settings: Dict[str, Any]


class AIConfigResponse(BaseModel):
    model_provider: str
    model_name: str
    langgraph_enabled: bool
    domain_routing_enabled: bool
    thinking_trace_enabled: bool


@router.get("/", response_model=SettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_user)):
    """
    Get all settings for the current user
    """
    from backend.ai_agent.data_adapter import get_adapter
    
    adapter = get_adapter()
    
    # Get user-specific settings
    user_settings = adapter.query("settings", {"user_id": current_user["id"]})
    
    # Merge with defaults
    settings = {
        "theme": "dark",
        "language": "en",
        "notifications_enabled": True,
        "auto_refresh": True,
        "refresh_interval": 30,
        "chart_animations": True,
        "show_thinking_trace": True,
        "compact_mode": False,
    }
    
    # Override with user settings
    for s in user_settings:
        settings[s.get("key")] = s.get("value")
    
    return SettingsResponse(settings=settings)


@router.put("/")
async def update_setting(
    setting: SettingUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a setting for the current user
    """
    from backend.ai_agent.data_adapter import get_adapter
    
    adapter = get_adapter()
    
    # Check if setting exists
    existing = adapter.query("settings", {
        "user_id": current_user["id"],
        "key": setting.key
    })
    
    if existing:
        adapter.update("settings", existing[0]["id"], {"value": setting.value})
    else:
        adapter.insert("settings", {
            "user_id": current_user["id"],
            "key": setting.key,
            "value": setting.value
        })
    
    return {"message": f"Setting '{setting.key}' updated successfully"}


@router.get("/ai-config", response_model=AIConfigResponse)
async def get_ai_config(current_user: dict = Depends(get_current_user)):
    """
    Get AI configuration settings
    """
    from backend.config import AI_CONFIG, LANGGRAPH_CONFIG
    
    return AIConfigResponse(
        model_provider=AI_CONFIG.get("model_provider", "ollama"),
        model_name=AI_CONFIG.get("ollama_model", "llama3.2:latest"),
        langgraph_enabled=LANGGRAPH_CONFIG.get("use_langgraph_agents", True),
        domain_routing_enabled=LANGGRAPH_CONFIG.get("enable_domain_routing", True),
        thinking_trace_enabled=LANGGRAPH_CONFIG.get("enable_thinking_trace", True)
    )


@router.put("/ai-config")
async def update_ai_config(
    config: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Update AI configuration (admin only)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    # Note: In production, this would update the config file or database
    # For now, we just validate and return success
    
    valid_keys = [
        "model_provider", "model_name", "langgraph_enabled",
        "domain_routing_enabled", "thinking_trace_enabled"
    ]
    
    invalid_keys = [k for k in config.keys() if k not in valid_keys]
    if invalid_keys:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid config keys: {invalid_keys}"
        )
    
    return {"message": "AI configuration updated", "config": config}


@router.get("/theme")
async def get_theme(current_user: dict = Depends(get_current_user)):
    """Get current theme setting"""
    settings = await get_settings(current_user)
    return {"theme": settings.settings.get("theme", "dark")}


@router.put("/theme")
async def update_theme(
    theme: str,
    current_user: dict = Depends(get_current_user)
):
    """Update theme setting"""
    if theme not in ["light", "dark", "system"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid theme. Use 'light', 'dark', or 'system'"
        )
    
    await update_setting(SettingUpdate(key="theme", value=theme), current_user)
    return {"theme": theme}


@router.get("/data-source")
async def get_data_source_info(current_user: dict = Depends(get_current_user)):
    """Get information about the current data source"""
    from backend.config import DATA_SOURCE, JSON_FILES
    from backend.ai_agent.data_adapter import get_adapter
    
    adapter = get_adapter()
    schema = adapter.get_schema()
    
    return {
        "source_type": DATA_SOURCE,
        "tables": list(schema.keys()),
        "file_paths": JSON_FILES if DATA_SOURCE == "json" else None
    }


@router.post("/refresh-data")
async def refresh_data(current_user: dict = Depends(get_current_user)):
    """
    Refresh data from source (reload JSON files or reconnect to database)
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    from backend.ai_agent.data_adapter import get_adapter
    
    adapter = get_adapter()
    adapter.refresh()
    
    return {"message": "Data refreshed successfully"}
