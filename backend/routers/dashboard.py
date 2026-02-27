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
        # Use EntityInvoices for sales data
        try:
            # Efficiently calculate total using SQL
            sales_res = adapter.execute_query('SELECT SUM("TotalAmount") as total FROM "EntityInvoices"')
            total_sales = 0.0
            if sales_res and sales_res[0].get("total"):
                total_sales = float(sales_res[0]["total"])
                
            kpis.append(KPICard(
                title="Total Sales",
                value=f"${total_sales:,.2f}",
                change=12.5,
                change_type="increase",
                icon="trending_up",
                color="#10B981"
            ))
        except Exception as e:
            # Fallback or specific error handling
            pass
    
    if "inventory" in user_agents:
        # Inventory table doesn't exist, using LookupItems as proxy for "System Items" or skip
        try:
            items_res = adapter.execute_query('SELECT COUNT(*) as count FROM "LookupItems"')
            total_items = 0
            if items_res and items_res[0].get("count"):
                total_items = int(items_res[0]["count"])
                
            kpis.append(KPICard(
                title="System Items",
                value=f"{total_items:,}",
                change=0,
                change_type="neutral",
                icon="category",
                color="#F59E0B"
            ))
        except:
             pass
    
    # Add general KPIs
    try:
        conversations = adapter.get_all("conversations")
        kpis.append(KPICard(
            title="AI Queries",
            value=f"{len(conversations):,}",
            change=8.7,
            change_type="increase",
            icon="chat",
            color="#6366F1"
        ))
    except:
        pass
        
    users = adapter.get_all("users")
    active_users = len(users) if users else 0
    kpis.append(KPICard(
        title="Active Users",
        value=f"{active_users:,}",
        change_type="neutral",
        icon="people",
        color="#8B5CF6"
    ))
    
    # Generate sample charts
    charts = []
    
    if "sales" in user_agents:
        try:
            # Top 10 Invoices by Amount
            sales_data = adapter.execute_query('SELECT "InvoiceNumber", "TotalAmount" FROM "EntityInvoices" ORDER BY "TotalAmount" DESC LIMIT 10')
            charts.append({
                "type": "bar",
                "title": "Top Invoices",
                "labels": [s.get("InvoiceNumber", f"Inv {i}") for i, s in enumerate(sales_data)],
                "datasets": [{
                    "label": "Amount",
                    "data": [float(s.get("TotalAmount") or 0) for s in sales_data],
                    "backgroundColor": ["#6366F1", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"] * 2
                }]
            })
        except:
            pass
    
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
