"""
Processing Agent - Execute tools and retrieve data
Handles SQL execution, calculations, and RAG retrieval
"""
import logging
from typing import Dict, Any, List, Optional

from backend.ai_agent.data_adapter import get_adapter

logger = logging.getLogger(__name__)


class ProcessingAgent:
    """Agent responsible for executing tools and retrieving data"""
    
    def __init__(self):
        self.adapter = get_adapter()
    
    async def execute(
        self,
        query: str,
        thinking_result: Dict[str, Any],
        allowed_agents: List[str]
    ) -> Dict[str, Any]:
        """
        Execute the selected tool based on thinking agent's analysis
        """
        tool = thinking_result.get("tool", "sql")
        domain_context = thinking_result.get("domain_context", {})
        parameters = thinking_result.get("parameters", {})
        
        logger.info(f"[PROCESSING AGENT] Executing tool: {tool}")
        logger.info(f"[PROCESSING AGENT] Domain context: {domain_context}")
        
        try:
            if tool == "sql":
                result = await self._execute_sql(query, domain_context, parameters)
            elif tool == "calculator":
                result = await self._execute_calculator(query, parameters)
            elif tool == "rag":
                result = await self._execute_rag(query)
            else:
                result = await self._execute_sql(query, domain_context, parameters)
            
            return {
                "data": result.get("data", []),
                "row_count": len(result.get("data", [])),
                "generated_query": result.get("query", ""),
                "tool_used": tool,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"[PROCESSING AGENT] Error executing {tool}: {e}")
            return {
                "data": [],
                "row_count": 0,
                "error": str(e),
                "tool_used": tool,
                "success": False
            }
    
    async def _execute_sql(
        self,
        query: str,
        domain_context: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute SQL-like query on data"""
        tables = domain_context.get("tables", [])
        limit = parameters.get("limit", 10)
        order = parameters.get("order", "desc")
        
        if not tables:
            tables = ["sales"]  # Default table
        
        query_lower = query.lower()
        
        # ====== SUBTABLE EXTRACTION (CHECK FIRST) ======
        # Map keywords to JSON keys in project_59
        subtable_map = {
            "cancel bank": ["custom_custom_doctypes_to_cancel_bank_guarantee"],
            "bank": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
            "guarantee": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
            "invoice": ["custom_doctypes_to_send_sales_invoice", "custom_doctypes_to_send_purchase_invoice"],
            "sales order": ["custom_doctypes_to_send_sales_order"],
            "purchase order": ["custom_doctypes_to_send_purchase_order"],
            "order": ["custom_doctypes_to_send_sales_order", "custom_doctypes_to_send_purchase_order"],
            "opportunity": ["custom_doctypes_opportinity", "custom_doctypes_to_send_opportinity", "custom_tax_opporunity"],
            "quotation": ["custom_doctypes_to_send_quotation", "custom_supplier_quotation"],
            "offer": ["custom_doctypes_to_send_offer_note"],
            "contract": ["custom_contract_modification_note_logs"],
            "modification": ["custom_contract_modification_note_logs"],
            "assay": ["custom_doctypes_to_send_estimated_assay"],
            "certificate": ["custom_request_cert"],
            "claim": ["custom_payment_claim_logs"],
            "payment": ["custom_payment_claim_logs"],
            "tax": ["custom_tax_status"],
            "hazard": ["custom_doctypes_to_send_hazarads"],
            "risk": ["custom_doctypes_to_send_hazarads"],
        }
        
        # Check if query targets a subtable
        target_key = None
        for keyword, keys in subtable_map.items():
            if keyword in query_lower:
                target_key = keys
                break
        
        # If subtable keyword found, extract from project_59
        if target_key:
            logger.info(f"[PROCESSING AGENT] Query targets sub-table: {target_key}")
            # Fetch full project data
            project_data = self.adapter.get_all("project_59")
            extracted_data = []
            
            for proj in project_data:
                for key in target_key:
                     if key in proj and isinstance(proj[key], list):
                         # Add project name to each item for context
                         items = proj[key]
                         for item in items:
                             if isinstance(item, dict):
                                 item["project_name_ref"] = proj.get("project_name", "")
                                 extracted_data.append(item)
            
            # Filter/Limit
            if extracted_data:
                # Sort if possible (look for 'totals' or 'amount')
                try:
                    extracted_data.sort(key=lambda x: float(x.get("totals", x.get("amount", 0))), reverse=(order=="desc"))
                except:
                    pass
                
                return {
                    "data": extracted_data[:limit],
                    "query": f"Extracted {target_key} from Project 59"
                }
        
        # ====== FALLBACK: GENERAL TABLE QUERY ======
        # Select best table based on query
        primary_table = tables[0]
        
        # Smart table selection
        if "project" in query_lower and "project_59" in tables:
            primary_table = "project_59"
        elif "inventory" in query_lower and "inventory" in tables:
            primary_table = "inventory"
        elif "sales" in query_lower:
            if "sales" in tables and self.adapter.get_all("sales"):
                primary_table = "sales"
            elif "project_59" in tables:
                primary_table = "project_59"
        
        # Build query based on query type
        if "top" in query_lower or "ranking" in query_lower or "project" in query_lower:
            # Ranking query
            if primary_table == "sales":
                sql = f"SELECT * FROM sales ORDER BY amount {order} LIMIT {limit}"
            elif primary_table == "inventory":
                sql = f"SELECT * FROM inventory ORDER BY quantity {order} LIMIT {limit}"
            elif primary_table == "project_59":
                sql = f"SELECT * FROM project_59 ORDER BY total_sales_amount {order} LIMIT {limit}"
            else:
                sql = f"SELECT * FROM {primary_table} LIMIT {limit}"
        
        elif "total" in query_lower or "sum" in query_lower:
            # Aggregation query - return all and let visualization handle
            sql = f"SELECT * FROM {primary_table}"
        
        else:
            # General query
            sql = f"SELECT * FROM {primary_table} LIMIT {limit}"
        
        logger.info(f"[PROCESSING AGENT] Generated SQL: {sql}")
        
        # Execute query on data adapter
        data = self.adapter.execute_query(sql)
        
        # If no SQL results, try direct table access
        if not data:
            data = self.adapter.get_all(primary_table)[:limit]
        
        return {
            "data": data,
            "query": sql
        }

    async def _execute_calculator(
        self,
        query: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute mathematical calculations"""
        import re
        
        result = None
        expression = None
        
        try:
            # Extract numbers from query
            numbers = re.findall(r'[\d.]+', query)
            
            if len(numbers) >= 2:
                num1, num2 = float(numbers[0]), float(numbers[1])
                
                query_lower = query.lower()
                
                if any(op in query_lower for op in ["add", "plus", "sum", "+"]):
                    result = num1 + num2
                    expression = f"{num1} + {num2}"
                
                elif any(op in query_lower for op in ["subtract", "minus", "-"]):
                    result = num1 - num2
                    expression = f"{num1} - {num2}"
                
                elif any(op in query_lower for op in ["multiply", "times", "*", "x"]):
                    result = num1 * num2
                    expression = f"{num1} × {num2}"
                
                elif any(op in query_lower for op in ["divide", "/"]):
                    result = num1 / num2 if num2 != 0 else 0
                    expression = f"{num1} ÷ {num2}"
                
                elif "percent" in query_lower or "%" in query:
                    result = (num1 / 100) * num2
                    expression = f"{num1}% of {num2}"
            
            if result is not None:
                return {
                    "data": [{"expression": expression, "result": result}],
                    "query": expression
                }
            
        except Exception as e:
            logger.error(f"Calculator error: {e}")
        
        return {"data": [], "query": "Unable to parse calculation"}
    
    async def _execute_rag(self, query: str) -> Dict[str, Any]:
        """Execute simple text-based retrieval (Basic RAG)"""
        # Search across all available tables for query terms
        results = []
        query_terms = [t.lower() for t in query.split() if len(t) > 3] # Filter small words
        
        try:
             # Get all tables defined in config or default to key ones
            from backend.config import JSON_FILES
            tables = list(JSON_FILES.keys())
            
            for table in tables:
                 # Skip system tables
                if table in ["users", "agents", "conversations", "settings"]:
                    continue
                    
                data = self.adapter.get_all(table)
                for row in data:
                    # Convert row to string for search
                    row_str = str(row).lower()
                    
                    # Score match based on term overlap
                    match_count = sum(1 for term in query_terms if term in row_str)
                    
                    if match_count > 0:
                        # Clone row and add context metadata
                        result_row = row.copy()
                        result_row["_source"] = table
                        result_row["_relevance"] = match_count
                        results.append(result_row)
            
            # Sort by relevance
            results.sort(key=lambda x: x["_relevance"], reverse=True)
            
            return {
                "data": results[:10], # Top 10 matches
                "query": f"Search for: {', '.join(query_terms)}"
            }
            
        except Exception as e:
            logger.error(f"[PROCESSING AGENT] RAG Error: {e}")
            return {
                "data": [],
                "error": str(e),
                "query": "RAG Search Failed"
            }
