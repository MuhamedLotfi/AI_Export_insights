"""
Visualization Agent - Generate charts and data visualizations
Automatically determines appropriate chart types based on data
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class VisualizationAgent:
    """Agent responsible for generating data visualizations"""
    
    def __init__(self):
        self.chart_colors = [
            "#6366F1",  # Indigo
            "#8B5CF6",  # Purple
            "#EC4899",  # Pink
            "#10B981",  # Emerald
            "#F59E0B",  # Amber
            "#3B82F6",  # Blue
            "#EF4444",  # Red
            "#14B8A6",  # Teal
        ]
    
    async def generate(
        self,
        query: str,
        data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate visualization configuration based on query and data
        """
        if not data:
            return {"chart_data": None}
        
        logger.info(f"[VISUALIZATION AGENT] Generating chart for {len(data)} data points")
        
        # Determine chart type
        chart_type = self._determine_chart_type(query, data)
        
        # Extract chart data
        chart_data = self._extract_chart_data(data, chart_type, query)
        
        if chart_data:
            logger.info(f"[VISUALIZATION AGENT] Generated {chart_type} chart")
        
        return {
            "chart_data": chart_data,
            "chart_type": chart_type
        }
    
    def _determine_chart_type(self, query: str, data: List[Dict]) -> str:
        """Determine the most appropriate chart type"""
        query_lower = query.lower()
        
        # Check for explicit chart mentions
        if any(kw in query_lower for kw in ["pie", "distribution", "breakdown"]):
            return "pie"
        
        if any(kw in query_lower for kw in ["line", "trend", "over time", "timeline"]):
            return "line"
        
        if any(kw in query_lower for kw in ["bar", "ranking", "top", "compare", "comparison"]):
            return "bar"
        
        # Infer from data structure
        if len(data) > 0:
            first_row = data[0]
            keys = list(first_row.keys())
            
            # If there's a date/time column, suggest line chart
            date_columns = ["date", "month", "year", "time", "period", "created_at"]
            if any(col in keys for col in date_columns):
                return "line"
            
            # If few items with numeric values, suggest pie
            if len(data) <= 6:
                return "pie"
            
            # Default to bar for rankings
            return "bar"
        
        return "bar"
    
    def _extract_chart_data(
        self,
        data: List[Dict],
        chart_type: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """Extract and format data for chart rendering"""
        if not data:
            return None
        
        # Find label and value columns
        first_row = data[0]
        keys = list(first_row.keys())
        
        # Identify label column (categorical)
        label_candidates = ["reference_name", "project_name", "title", "customer", "supplier", "item", "product", "category", "label", "type", "reference_type", "doctype", "description", "doc_details", "agent", "project", "name"]
        label_col = None
        for col in label_candidates:
            if col.lower() in [k.lower() for k in keys]:
                label_col = next(k for k in keys if k.lower() == col.lower())
                break
        
        if not label_col:
            # Use first string column
            for k in keys:
                if isinstance(first_row.get(k), str) and k.lower() != "id":
                    label_col = k
                    break
        
        # Identify value column (numeric)
        value_candidates = ["amount", "total", "quantity", "value", "count", "sales", "revenue", "price", "cost", "totals", "profit", "margin"]
        value_col = None
        
        # 1. Try exact match
        for col in value_candidates:
            if col.lower() in [k.lower() for k in keys]:
                value_col = next(k for k in keys if k.lower() == col.lower())
                break
        
        # 2. Try partial match for value columns (e.g. "total_sales_amount" contains "amount")
        if not value_col:
            for k in keys:
                 k_lower = k.lower()
                 if isinstance(first_row.get(k), (int, float)) and k.lower() != "id":
                     if any(vc in k_lower for vc in value_candidates):
                          value_col = k
                          break
                          
        # 3. Use first numeric column as fallback
        if not value_col:
            for k in keys:
                val = first_row.get(k)
                if isinstance(val, (int, float)) and k.lower() != "id" and not k.lower().endswith("id"):
                    value_col = k
                    break
        
        if not label_col or not value_col:
            logger.warning("[VISUALIZATION AGENT] Could not identify label or value columns")
            return None
        
        # Build chart data
        labels = [str(row.get(label_col, "")) for row in data]
        values = [float(row.get(value_col, 0)) for row in data]
        
        # Assign colors
        colors = [self.chart_colors[i % len(self.chart_colors)] for i in range(len(labels))]
        
        chart_data = {
            "type": chart_type,
            "title": self._generate_chart_title(query, chart_type),
            "labels": labels,
            "datasets": [
                {
                    "label": value_col.replace("_", " ").title(),
                    "data": values,
                    "backgroundColor": colors,
                    "borderColor": colors,
                }
            ],
            "options": self._get_chart_options(chart_type),
            "metadata": {
                "label_column": label_col,
                "value_column": value_col,
                "data_count": len(data)
            }
        }
        
        return chart_data
    
    def _generate_chart_title(self, query: str, chart_type: str) -> str:
        """Generate a title for the chart"""
        # Capitalize first letter of query
        title = query.strip()
        if title:
            title = title[0].upper() + title[1:]
        
        # Remove question marks
        title = title.rstrip("?")
        
        # Truncate if too long
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
    
    def _get_chart_options(self, chart_type: str) -> Dict[str, Any]:
        """Get chart-specific options"""
        base_options = {
            "responsive": True,
            "maintainAspectRatio": True,
            "animation": True
        }
        
        if chart_type == "pie":
            return {
                **base_options,
                "cutout": "50%",  # Donut style
                "showLegend": True
            }
        
        elif chart_type == "line":
            return {
                **base_options,
                "fill": True,
                "tension": 0.4,  # Smooth curves
                "showGridLines": True
            }
        
        elif chart_type == "bar":
            return {
                **base_options,
                "horizontal": False,
                "showGridLines": True,
                "barPercentage": 0.8
            }
        
        return base_options
    
    def format_value(self, value: float, format_type: str = "number") -> str:
        """Format a value for display"""
        if format_type == "currency":
            return f"${value:,.2f}"
        elif format_type == "percent":
            return f"{value:.1f}%"
        elif format_type == "integer":
            return f"{int(value):,}"
        else:
            return f"{value:,.2f}"
