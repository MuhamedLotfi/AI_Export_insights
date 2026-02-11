import json
import os
from typing import Dict, Any, List

from backend.config import JSON_FILES


class PromptManager:
    """Manages system prompts and context for the AI Agent"""
    
    VERSION = "3.0.0"
    
    def __init__(self):
        self._schema_cache = None
        self._nested_schema_cache = None
        self._load_schema()
    
    def _load_schema(self):
        """Dynamically load schema from JSON files, including nested structure detection"""
        schema = {}
        nested_schema = {}
        
        try:
            for name, path in JSON_FILES.items():
                if os.path.exists(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, dict) and "data" in data:
                                rows = data["data"]
                                if rows and len(rows) > 0:
                                    first_row = rows[0]
                                    # Get top-level keys
                                    schema[name] = list(first_row.keys())
                                    
                                    # Detect nested arrays (subtables)
                                    nested_info = {}
                                    for key, value in first_row.items():
                                        if isinstance(value, list) and len(value) > 0:
                                            count = len(value)
                                            if isinstance(value[0], dict):
                                                sub_keys = list(value[0].keys())
                                                nested_info[key] = {
                                                    "count": count,
                                                    "fields": sub_keys
                                                }
                                    if nested_info:
                                        nested_schema[name] = nested_info
                                        
                            elif isinstance(data, list) and len(data) > 0:
                                schema[name] = list(data[0].keys())
                    except Exception as e:
                        print(f"Error loading schema for {name}: {e}")
        except Exception as e:
            print(f"Error loading schemas: {e}")
            
        self._schema_cache = schema
        self._nested_schema_cache = nested_schema

    def get_system_prompt(self, user_role: str = "user") -> str:
        """Generate the system prompt based on user role and current schema"""
        
        schema_str = self._format_schema()
        nested_str = self._format_nested_schema()
        
        prompt = f"""You are an advanced AI Data Analyst for the 'AI Export Insights' platform. 
Your goal is to analyze business data and provide concise, actionable insights.
You MUST respond with detailed information from the data provided to you.

## System Configuration
- **Prompt Version**: {self.VERSION}
- **User Role**: {user_role}

## Database Schema (JSON Data Sources)
You have access to the following data structures. Use these field names PRECISELY when discussing data.
{schema_str}

## Nested Data Structure (Subtables)
The project_59 table contains nested arrays (subtables) with detailed records. When users ask about these, the data has already been extracted for you.
{nested_str}

## Data Semantics & Business Definitions
- **project_59**: The primary project tracking table. Contains one project record with deeply nested sub-tables.
  - `total_sales_amount`: Total revenue (إجمالي المبيعات) = 32,600,000
  - `total_purchase_cost`: Total expenses (إجمالي المشتريات)
  - `total_billed_amount`: Total invoiced amount (إجمالي الفواتير)
  - `gross_margin`: Revenue minus costs (هامش الربح)
  - `custom_project_profitability`: Profit percentage (نسبة الربحية)
  - `project_name`: Descriptive title (اسم المشروع)
  - `customer`: Client name (العميل) - الإدارة العامة للمرور
  - `status`: Current state (الحالة) - "In Progress"
  - Subtable items typically have: `reference_type`, `reference_name`, `doc_details`, `totals`

## Communication Style
- **Be concise and professional**: Avoid fluff. Get straight to the point.
- **Use bullet points**: For any list of 3+ items.
- **Use tables for structured data**: When showing multiple records, use markdown tables.
- **Highlight key values in bold**: e.g., "The **total sales** is **32,600,000**"
- **Always mention record counts**: e.g., "Found **22 opportunities**"
- **Include totals/sums when numeric data is present**: Sum up values automatically.
- **Format large numbers with commas**: e.g., 32,600,000 not 32600000.
- **If data contains Arabic text, preserve it**: Don't translate data values.

## Response Structure
When answering queries:
1. **Summary line**: One sentence answering the question directly.
2. **Data table or bullet list**: Show the actual records.
3. **Total/Aggregate**: If numeric, show the total.
4. **Follow-up suggestion**: Guide the user to related queries.

## Important Rules
- **NEVER say "no data found" if data is provided to you**. Always analyze what's given.
- **ALWAYS reference specific values from the data** (numbers, names, references).
- **When data has `reference_name` and `doc_details`, always show both**.
- **When data has `totals`, always show it and compute the grand total**.

"""
        return prompt

    def _format_schema(self) -> str:
        """Format schema for the prompt"""
        if not self._schema_cache:
            return "No schema available."
            
        lines = []
        for table, fields in self._schema_cache.items():
            # filter out internal fields
            public_fields = [f for f in fields if not f.startswith("_")]
            # Separate scalar fields from list fields
            scalar_fields = []
            list_fields = []
            for f in public_fields:
                if self._nested_schema_cache and table in self._nested_schema_cache and f in self._nested_schema_cache[table]:
                    list_fields.append(f)
                else:
                    scalar_fields.append(f)
            
            # Show scalar fields (limit to 20)
            if len(scalar_fields) > 20:
                display_fields = scalar_fields[:20] + ["..."]
            else:
                display_fields = scalar_fields
            
            lines.append(f"- **{table}** (scalar fields): {', '.join(display_fields)}")
            
            # Show nested fields summary
            if list_fields:
                lines.append(f"  - **Nested arrays**: {', '.join(list_fields)}")
        
        return "\n".join(lines)

    def _format_nested_schema(self) -> str:
        """Format nested schema information for the prompt"""
        if not self._nested_schema_cache:
            return "No nested data structures detected."
        
        lines = []
        for table, nested_info in self._nested_schema_cache.items():
            lines.append(f"### {table} subtables:")
            for key, info in nested_info.items():
                count = info["count"]
                fields = info["fields"]
                # Show key fields only 
                important_fields = [f for f in fields if f in ("reference_type", "reference_name", "doc_details", "totals", "customer", "name", "idx")]
                other_count = len(fields) - len(important_fields)
                
                field_str = ", ".join(important_fields)
                if other_count > 0:
                    field_str += f" (+{other_count} more)"
                
                lines.append(f"- `{key}` ({count} items): {field_str}")
        
        return "\n".join(lines)


# Singleton
_prompt_manager = None

def get_prompt_manager():
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
