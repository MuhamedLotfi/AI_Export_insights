"""
Dashboard API Router
Provides dashboard analytics and KPIs
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from backend.routers.auth import get_current_user

router = APIRouter()


class KPICard(BaseModel):
    title: str
    value: str
    change: Optional[float] = None
    change_type: Optional[str] = None  # "increase", "decrease", "neutral"
    icon: str
    color: str


class DashboardResponse(BaseModel):
    kpis: List[KPICard]
    charts: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    system_status: Dict[str, Any]


@router.get("/", response_model=DashboardResponse)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """
    Get dashboard data with KPIs, charts, and recent activity
    """
    from backend.ai_agent.data_adapter import get_adapter
    from backend.ai_agent.auth_service import get_auth_service
    
    adapter = get_adapter()
    auth_service = get_auth_service()
    
    # Get user's allowed agents
    user_agents = auth_service.get_user_domain_agents(current_user["id"])
    
    # Calculate KPIs based on allowed domains
    kpis = []
    
    if "sales" in user_agents:
        sales_data = adapter.get_all("sales")
        total_sales = sum(s.get("amount", 0) for s in sales_data)
        kpis.append(KPICard(
            title="Total Sales",
            value=f"${total_sales:,.2f}",
            change=12.5,
            change_type="increase",
            icon="trending_up",
            color="#10B981"
        ))
    
    if "inventory" in user_agents:
        inventory_data = adapter.get_all("inventory")
        total_items = len(inventory_data)
        kpis.append(KPICard(
            title="Inventory Items",
            value=f"{total_items:,}",
            change=-3.2,
            change_type="decrease",
            icon="inventory_2",
            color="#F59E0B"
        ))
    
    # Add general KPIs
    conversations = adapter.get_all("conversations")
    kpis.append(KPICard(
        title="AI Queries",
        value=f"{len(conversations):,}",
        change=8.7,
        change_type="increase",
        icon="chat",
        color="#6366F1"
    ))
    
    users = adapter.get_all("users")
    kpis.append(KPICard(
        title="Active Users",
        value=f"{len(users):,}",
        change_type="neutral",
        icon="people",
        color="#8B5CF6"
    ))
    
    # Generate sample charts
    charts = []
    
    if "sales" in user_agents:
        sales_data = adapter.get_all("sales")[:10]
        charts.append({
            "type": "bar",
            "title": "Top Sales",
            "labels": [s.get("name", f"Item {i}") for i, s in enumerate(sales_data)],
            "datasets": [{
                "label": "Sales",
                "data": [s.get("amount", 0) for s in sales_data],
                "backgroundColor": ["#6366F1", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"]
            }]
        })
    
    # Recent activity
    recent_activity = [
        {"action": "Query", "description": "User queried sales data", "time": "2 mins ago"},
        {"action": "Login", "description": "User logged in", "time": "1 hour ago"},
        {"action": "Export", "description": "Data exported to CSV", "time": "3 hours ago"},
    ]
    
    # System status
    system_status = {
        "api": "healthy",
        "data_source": "connected",
        "ai_service": "ready"
    }
    
    return DashboardResponse(
        kpis=kpis,
        charts=charts,
        recent_activity=recent_activity,
        system_status=system_status
    )


@router.get("/kpis", response_model=List[KPICard])
async def get_kpis(current_user: dict = Depends(get_current_user)):
    """Get KPI cards only"""
    dashboard = await get_dashboard(current_user)
    return dashboard.kpis


@router.get("/charts")
async def get_charts(current_user: dict = Depends(get_current_user)):
    """Get charts only"""
    dashboard = await get_dashboard(current_user)
    return {"charts": dashboard.charts}


@router.get("/activity")
async def get_activity(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get recent activity"""
    from backend.ai_agent.data_adapter import get_adapter
    
    adapter = get_adapter()
    
    # Get recent conversations as activity
    conversations = adapter.get_all("conversations")
    
    activity = []
    for conv in conversations[:limit]:
        activity.append({
            "action": "Query",
            "description": conv.get("query", "")[:50] + "...",
            "time": conv.get("timestamp", ""),
            "user_id": conv.get("user_id")
        })
    
    return {"activity": activity}
