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
        data: List[Dict[str, Any]],
        tool_used: str = "sql"
    ) -> Dict[str, Any]:
        """
        Generate visualization configuration based on query and data
        """
        # Skip charting for pure retrieval results
        if tool_used == "rag" or not data:
            return {"chart_data": None}
            
        # Strip internal metadata keys
        clean_data = []
        for row in data:
            clean_data.append({k: v for k, v in row.items() if not k.startswith("_")})
        
        logger.info(f"[VISUALIZATION AGENT] Generating chart for {len(clean_data)} data points")
        
        # Determine chart type
        chart_type = self._determine_chart_type(query, clean_data)
        
        if chart_type == "none":
            logger.info("[VISUALIZATION AGENT] Query intent is listing/details - skipping chart")
            return {"chart_data": None, "chart_type": "none"}
        
        # Extract chart data
        chart_data = self._extract_chart_data(clean_data, chart_type, query)
        
        if chart_data:
            logger.info(f"[VISUALIZATION AGENT] Generated {chart_type} chart")
        
        return {
            "chart_data": chart_data,
            "chart_type": chart_type
        }
    
    def _determine_chart_type(self, query: str, data: List[Dict]) -> str:
        """Determine the most appropriate chart type"""
        query_lower = query.lower()
        
        # Skip structural/detail-only queries
        detail_keywords = ["تفاصيل", "details", "اذكر", "list", "عرض", "show", "وصف", "describe", "معلومات", "info"]
        if any(kw in query_lower for kw in detail_keywords):
            # If the query is just asking to list things, a chart often adds noise
            return "none"
            
        # Check for explicit chart mentions (English and Arabic)
        if any(kw in query_lower for kw in ["pie", "distribution", "breakdown", "دائري", "توزيع", "حصة"]):
            return "pie"
        
        if any(kw in query_lower for kw in ["line", "trend", "over time", "timeline", "خط", "اتجاه", "زمني"]):
            return "line"
        
        if any(kw in query_lower for kw in ["bar", "ranking", "top", "compare", "comparison", "شريطي", "ترتيب", "رسم", "مقارنة"]):
            return "bar"
        
        # Infer from data structure
        if len(data) > 0:
            first_row = data[0]
            keys = list(first_row.keys())
            
            # If there's a date/time column among the primary columns (first 2), suggest line chart
            date_keywords = ["date", "month", "year", "time", "period", "created_at"]
            from datetime import datetime as _dt_check, date as _date_check
            for col in keys[:2]:  # Only check primary (first 2) columns
                col_lower = col.lower()
                val = first_row.get(col)
                if any(kw in col_lower for kw in date_keywords) or isinstance(val, (_dt_check, _date_check)):
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
        # Priority-ordered: exact report column names → substring patterns → first string column
        LABEL_EXACT = [
            # Executive Dashboard
            "Client Name", "الجهة / الشركة", "Responsible Department",
            # Cash Flow & Liquidity
            "Financial Period",
            # Departmental Yield
            "Department Name",
            # Budget Variance
            "Client Entity", "Order Number", "Financial Status",
            # Project Lifecycle
            "Incoming / Request No.", "Project / Operation No.",
            "Operation Description", "Handling Department", "Lifecycle Phase",
            # P&L
            "ProjectName", "ClientEntity", "Financial Status",
            # Revenue Bottlenecks
            "Pipeline Bottleneck Stage",
            # Generic fallbacks
            "Account Tier", "Board Recommendation",
        ]
        # Substrings that strongly indicate a label column
        LABEL_SUBSTRINGS = [
            "name", "entity", "department", "project", "stage", "status",
            "phase", "description", "number", "category", "type", "client",
            "supplier", "reference", "title", "label", "period",
        ]

        label_col = None
        keys_lower = [k.lower() for k in keys]

        # 1. Match exact known column names (case-insensitive)
        for candidate in LABEL_EXACT:
            if candidate.lower() in keys_lower:
                label_col = keys[keys_lower.index(candidate.lower())]
                break

        # 2. Match by substring in column name, excluding ID and numeric columns
        if not label_col:
            for k in keys:
                k_lower = k.lower()
                val = first_row.get(k)
                if not isinstance(val, (int, float)) and k_lower not in ("id",) and not k_lower.endswith("id"):
                    if any(sub in k_lower for sub in LABEL_SUBSTRINGS):
                        label_col = k
                        break

        # 3. Fall back: first string column that is not an ID field
        if not label_col:
            for k in keys:
                val = first_row.get(k)
                if isinstance(val, str) and k.lower() not in ("id",) and not k.lower().endswith("id"):
                    label_col = k
                    break

        # 4. Fall back: first datetime column (e.g. DATE_TRUNC results)
        if not label_col:
            from datetime import datetime, date
            for k in keys:
                val = first_row.get(k)
                if isinstance(val, (datetime, date)) and k.lower() not in ("id",):
                    label_col = k
                    break
        
        # Identify value column (numeric) — schema-aware priority ordering
        # Priority 1: Named EGP revenue/financial columns (highest business value)
        EGP_PRIORITY = [
            # Highest-signal: net/profit comes first (most meaningful KPI)
            "Net Project Profit (EGP)",
            "Net Department Value (EGP)",
            "Unbilled Revenue (EGP)",
            "Trapped Potential Value (EGP)",
            "Total Invoiced Revenue (EGP)",
            "Gross Revenue Yield (EGP)",
            "Gross Revenue from Client (EGP)",
            "Realized Revenue Paid (EGP)",
            "Actual Realized Cash (EGP)",
            "Gross Expected Invoice Value (EGP)",
            "Contracted Value (EGP)",
            "Total Billed by Finance (EGP)",
            "Collected Cash (EGP)",
            "Supplier Costs (EGP)",
            "Gross Supplier Costs (EGP)",
            "Avg Revenue Per Project (EGP)",
        ]
        # Priority 2: Percentage / ratio columns
        PCT_PRIORITY = [
            "Billing Completion (%)",
            "Profit Margin (%)",
        ]
        # Priority 3: Integer / count columns
        COUNT_PRIORITY = [
            "Total Projects Handled",
            "Active Projects (Operations)",
            "Invoices Issued",
            "Number of Original Requests",
            "Days to Activate Project",
        ]

        value_col = None
        value_format = "number"

        # 1. Exact EGP column match → currency
        for candidate in EGP_PRIORITY:
            if candidate.lower() in keys_lower:
                value_col = keys[keys_lower.index(candidate.lower())]
                value_format = "currency"
                break

        # 2. Exact % column match → percent
        if not value_col:
            for candidate in PCT_PRIORITY:
                if candidate.lower() in keys_lower:
                    value_col = keys[keys_lower.index(candidate.lower())]
                    value_format = "percent"
                    break

        # 3. Exact count column → integer
        if not value_col:
            for candidate in COUNT_PRIORITY:
                if candidate.lower() in keys_lower:
                    value_col = keys[keys_lower.index(candidate.lower())]
                    value_format = "integer"
                    break

        # 4. Partial-match fallback on column name substrings + type (int/float)
        VALUE_CURRENCY_KW  = ["egp", "revenue", "profit", "cost", "yield", "cash", "value", "amount", "price", "billed", "contracted", "realized", "potential"]
        VALUE_PERCENT_KW   = ["%", "percent", "pct", "margin", "ratio", "completion", "rate"]
        VALUE_INTEGER_KW   = ["count", "number", "volume", "qty", "quantity", "projects", "invoices", "requests", "days"]

        if not value_col:
            for k in keys:
                val = first_row.get(k)
                if not isinstance(val, (int, float)) or k.lower() in ("id",) or k.lower().endswith("id"):
                    continue
                k_lower = k.lower()
                if any(kw in k_lower for kw in VALUE_CURRENCY_KW):
                    value_col = k
                    value_format = "currency"
                    break
                if any(kw in k_lower for kw in VALUE_PERCENT_KW):
                    value_col = k
                    value_format = "percent"
                    break
                if any(kw in k_lower for kw in VALUE_INTEGER_KW):
                    value_col = k
                    value_format = "integer"
                    break

        # 5. Last-resort: first numeric column
        if not value_col:
            for k in keys:
                val = first_row.get(k)
                if isinstance(val, (int, float)) and k.lower() not in ("id",) and not k.lower().endswith("id"):
                    value_col = k
                    break

        if not label_col or not value_col:
            logger.warning("[VISUALIZATION AGENT] Could not identify label or value columns from data")
            return None
            
        # Determine axis titles
        x_axis_title = label_col.replace("_", " ").title()
        y_axis_title = value_col.replace("_", " ").title()
        
        # Build tabular rendering properties
        show_data_table = len(data) >= 1 and len(keys) >= 2
        show_legend = chart_type == "pie" or (chart_type == "bar" and len(data) <= 6)
        
        # Build chart data with safe float conversion and datetime-aware label formatting
        from datetime import datetime as _dt, date as _date
        def _format_label(val):
            if isinstance(val, _dt):
                return val.strftime("%Y-%m")
            if isinstance(val, _date):
                return val.strftime("%Y-%m")
            return str(val) if val is not None else ""

        labels = [_format_label(row.get(label_col)) for row in data]

        # Serialize datetime values in data rows for JSON transport
        serialized_data = []
        for row in data:
            clean = {}
            for k, v in row.items():
                if isinstance(v, (_dt, _date)):
                    clean[k] = v.strftime("%Y-%m-%d")
                else:
                    clean[k] = v
            serialized_data.append(clean)
        
        values = []
        for row in data:
            val = row.get(value_col)
            try:
                values.append(float(val) if val is not None else 0.0)
            except (ValueError, TypeError):
                values.append(0.0)
                
        # --- PHASE 7: Prevent Zero-Sum Chart Rendering ---
        # If all numerical values are exactly 0, skip the chart but still show the data table.
        total_absolute_value = sum(abs(v) for v in values)
        if total_absolute_value == 0:
            logger.info(f"[VISUALIZATION AGENT] All values for {value_col} are 0. Showing table only.")
            table_only = {
                "type": "table",
                "title": self._generate_chart_title(query, "table"),
                "show_data_table": True,
                "show_legend": False,
                "labels": [],
                "datasets": [],
                "metadata": {
                    "label_column": label_col,
                    "value_column": value_col,
                    "data_count": len(data),
                },
                "data_columns": keys,
                "data_rows": serialized_data,
            }
            return table_only
        
        # Assign colors
        colors = [self.chart_colors[i % len(self.chart_colors)] for i in range(len(labels))]
        chart_data = {
            "type": chart_type,
            "title": self._generate_chart_title(query, chart_type),
            "show_legend": show_legend,
            "show_data_table": show_data_table,
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
                "x_axis_title": x_axis_title,
                "y_axis_title": y_axis_title,
                "value_format": value_format,
                "data_count": len(data)
            }
        }
        
        # Include row data specifically for the data table
        if show_data_table:
            chart_data["data_columns"] = keys
            chart_data["data_rows"] = serialized_data
            
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
            from backend.config import DISPLAY_CURRENCY
            return f"{value:,.2f} {DISPLAY_CURRENCY}"
        elif format_type == "percent":
            return f"{value:.1f}%"
        elif format_type == "integer":
            return f"{int(value):,}"
        else:
            return f"{value:,.2f}"
