"""
Coordinator Agent - Format final response and extract insights
Aggregates results from other agents and produces coherent output
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.ai_agent.llm_service import get_llm_service

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """Agent responsible for coordinating results and formatting responses"""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    async def format_response(
        self,
        query: str,
        thinking_result: Dict[str, Any],
        processing_result: Dict[str, Any],
        visualization: Dict[str, Any],
        history: List[Dict] = []
    ) -> Dict[str, Any]:
        """
        Coordinate all agent results into a final response
        """
        logger.info("[COORDINATOR AGENT] Formatting final response")
        
        # Extract data
        data = processing_result.get("data", [])
        row_count = processing_result.get("row_count", 0)
        tool_used = processing_result.get("tool_used", "unknown")
        
        # Build context for LLM
        context = {
            "query_type": thinking_result.get("query_type"),
            "allowed_domains": thinking_result.get("allowed_domains", []),
            "tool_used": tool_used,
            "tool_query": processing_result.get("generated_query", ""),
            "history": history
        }
        
        # Generate answer via LLM
        answer = await self._generate_answer(query, data, context)
        
        # Extract insights (keep rule-based as backup/structure)
        # insights = self._extract_insights(data, thinking_result)
        insights = []
        
        # Generate recommendations (keep rule-based as backup/structure)
        # recommendations = self._generate_recommendations(data, thinking_result)
        recommendations = []
        
        return {
            "answer": answer,
            "insights": insights,
            "recommendations": recommendations,
            "summary": "", # self._generate_summary(data, row_count),
            "metadata": {
                "query_type": thinking_result.get("query_type"),
                "domains_used": thinking_result.get("allowed_domains", []),
                "tool_used": tool_used,
                "data_points": row_count,
                "has_visualization": visualization.get("chart_data") is not None,
                "timestamp": datetime.now().isoformat(),
                "prompt_version": self.llm_service.prompt_manager.VERSION
            }
        }
    
    async def _generate_answer(
        self,
        query: str,
        data: List[Dict],
        context: Dict[str, Any]
    ) -> str:
        """Generate a natural language answer using LLM"""
        return await self.llm_service.generate_response(query, data, context)

    def _extract_insights(
        self,
        data: List[Dict],
        thinking_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract key insights from the data"""
        insights = []
        
        if not data:
            return insights
        
        first_row = data[0]
        value_col = self._find_value_column(first_row)
        name_col = self._find_name_column(first_row)
        
        if value_col:
            values = [row.get(value_col, 0) for row in data if isinstance(row.get(value_col), (int, float))]
            
            if values:
                max_val = max(values)
                min_val = min(values)
                avg_val = sum(values) / len(values)
                
                # Top performer insight
                max_row = next((row for row in data if row.get(value_col) == max_val), None)
                if max_row and name_col:
                    insights.append({
                        "type": "top_performer",
                        "title": "Top Performer",
                        "value": f"{max_row.get(name_col)} ({max_val:,.2f})",
                        "icon": "star"
                    })
                
                # Average insight
                insights.append({
                    "type": "average",
                    "title": "Average",
                    "value": f"{avg_val:,.2f}",
                    "icon": "analytics"
                })
                
                # Range insight
                insights.append({
                    "type": "range",
                    "title": "Range",
                    "value": f"{min_val:,.2f} - {max_val:,.2f}",
                    "icon": "swap_vert"
                })
        
        return insights
    
    def _generate_recommendations(
        self,
        data: List[Dict],
        thinking_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations"""
        recommendations = []
        
        domains = thinking_result.get("allowed_domains", [])
        query_type = thinking_result.get("query_type", "general")
        
        if "sales" in domains:
            recommendations.append({
                "title": "Sales Optimization",
                "description": "Focus on top-performing items to maximize revenue",
                "priority": "high",
                "icon": "trending_up"
            })
        
        if "inventory" in domains:
            recommendations.append({
                "title": "Inventory Management",
                "description": "Review stock levels to prevent stockouts",
                "priority": "medium",
                "icon": "inventory"
            })
        
        if query_type == "ranking":
            recommendations.append({
                "title": "Performance Review",
                "description": "Analyze bottom performers for improvement opportunities",
                "priority": "medium",
                "icon": "assessment"
            })
        
        return recommendations
    
    def _generate_summary(self, data: List[Dict], row_count: int) -> str:
        """Generate a brief summary"""
        if row_count == 0:
            return "No data found"
        elif row_count == 1:
            return "Found 1 record"
        else:
            return f"Found {row_count} records"
    
    def _find_name_column(self, row: Dict) -> Optional[str]:
        """Find the name/label column in a row"""
        candidates = ["name", "item", "product", "category", "description", "title", "label", "project_name"]
        for col in candidates:
            if col in row:
                return col
        return None
    
    def _find_value_column(self, row: Dict) -> Optional[str]:
        """Find the value/numeric column in a row"""
        candidates = ["amount", "total", "quantity", "value", "count", "sales", "revenue", "price", "total_sales_amount"]
        for col in candidates:
            if col in row:
                return col
        
        # Fallback to any numeric column
        for key, val in row.items():
            if isinstance(val, (int, float)) and key != "id":
                return key
        
        return None

