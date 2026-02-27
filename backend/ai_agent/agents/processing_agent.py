"""
Processing Agent - Execute tools and retrieve data
Handles SQL execution, calculations, and RAG retrieval
Enhanced with Arabic keyword support and deep nested data extraction
"""
import logging
from typing import Dict, Any, List, Optional

from backend.ai_agent.data_adapter import get_adapter

logger = logging.getLogger(__name__)


class ProcessingAgent:
    """Agent responsible for executing tools and retrieving data"""
    
    # Bilingual keyword → Table Name mapping (English + Arabic)
    # Maps user keywords to actual PostgreSQL tables
    SUBTABLE_MAP = {
        # Bank Guarantees (Not explicitly found in schema, mapping to best guesses or leaving empty if strict)
        # Using 'CompanyContracts' or 'Contracts' as they might contain guarantee info?
        # Or 'PaymentOrders' for financial instruments? 
        # For now, mapping known tables.
        
        # Invoices
        "sales invoice": ["EntityInvoices"],
        "فاتورة مبيعات": ["EntityInvoices"],
        "فواتير المبيعات": ["EntityInvoices"],
        "purchase invoice": ["PaymentOrderInvoices"], # Assuming PaymentOrderInvoices relates to purchases
        "فاتورة مشتريات": ["PaymentOrderInvoices"],
        "فواتير المشتريات": ["PaymentOrderInvoices"],
        "invoice": ["EntityInvoices", "PaymentOrderInvoices"],
        "فاتورة": ["EntityInvoices", "PaymentOrderInvoices"],
        "فواتير": ["EntityInvoices", "PaymentOrderInvoices"],
        
        # Orders
        "sales order": ["AssignmentOrders"], # Best guess for sales orders
        "أمر بيع": ["AssignmentOrders"],
        "أوامر البيع": ["AssignmentOrders"],
        "purchase order": ["PaymentOrders"], # Assuming PaymentOrders relates to purchasing
        "أمر شراء": ["PaymentOrders"],
        "أوامر الشراء": ["PaymentOrders"],
        "order": ["AssignmentOrders", "PaymentOrders"],
        "طلب": ["AssignmentOrders", "PaymentOrders"],
        
        # Opportunities / Letters -> Requests? or Operations?
        "opportunity": ["Requests", "Operations"],
        "فرصة": ["Requests", "Operations"],
        "فرص": ["Requests", "Operations"],
        "خطابات": ["Requests"],
        "خطاب": ["Requests"],
        
        # Quotations
        "quotation": ["PriceOffers", "IndicativeQuotations"],
        "عرض سعر": ["PriceOffers", "IndicativeQuotations"],
        "عرض أسعار": ["PriceOffers", "IndicativeQuotations"],
        "عروض": ["PriceOffers", "IndicativeQuotations"],
        
        # Contracts
        "contract": ["Contracts", "CompanyContracts"],
        "عقد": ["Contracts", "CompanyContracts"],
        "contracts": ["Contracts", "CompanyContracts"],
        "عقود": ["Contracts", "CompanyContracts"],
        
        # Claims
        "claim": ["PaymentOrderClaims"],
        "مطالبة": ["PaymentOrderClaims"],
        "مطالبات": ["PaymentOrderClaims"],
        "claims": ["PaymentOrderClaims"],
        
        # Tax
        "tax": ["TaxExemptions", "TaxExemptionInvoices"],
        "ضريبة": ["TaxExemptions"],
        "ضرائب": ["TaxExemptions"],
        
        # Operations
        "operation": ["Operations"],
        "عملية": ["Operations"],
        "operations": ["Operations"],
        "عمليات": ["Operations"],
        
        # Lookups
        "lookup": ["Lookups", "LookupItems"],
        
        # Users/Roles
        "user": ["Users"],
        "role": ["Roles"],
        
        # Dues / Entitlements / Disbursements (مستحقات / صرف)
        "مستحقات": ["PaymentOrders", "PaymentOrderClaims", "PaymentOrderDeductions"],
        "صرف": ["PaymentOrders", "PaymentOrderClaims"],
        "صرف مستحقات": ["PaymentOrders", "PaymentOrderClaims", "PaymentOrderDeductions"],
        "مستحقات الضباط": ["PaymentOrders", "PaymentOrderClaims"],
        "dues": ["PaymentOrders", "PaymentOrderClaims", "PaymentOrderDeductions"],
        "entitlements": ["PaymentOrders", "PaymentOrderClaims"],
        "disbursement": ["PaymentOrders", "PaymentOrderClaims"],
        "payment": ["PaymentOrders", "PaymentOrderClaims"],
        "دفع": ["PaymentOrders", "PaymentOrderClaims"],
        "مدفوعات": ["PaymentOrders", "PaymentOrderClaims"],
        "مستخلص": ["PaymentOrderClaims", "PaymentOrderClaimItems"],
    }
    
    # Human-readable names for subtable keys (for response context)
    SUBTABLE_LABELS = {
        "custom_doctypes_opportinity": "الفرص والخطابات (Opportunities)",
        "custom_doctypes_to_send_opportinity": "الفرص المرسلة (Sent Opportunities)",
        "custom_tax_opporunity": "فرص ضريبية (Tax Opportunities)",
        "custom_doctypes_to_send_bank_guarantee": "خطابات الضمان البنكية (Bank Guarantees)",
        "custom_custom_doctypes_to_cancel_bank_guarantee": "إلغاء خطابات الضمان (Cancel Bank Guarantees)",
        "custom_doctypes_to_send_sales_order": "أوامر البيع (Sales Orders)",
        "custom_doctypes_to_send_purchase_order": "أوامر الشراء (Purchase Orders)",
        "custom_doctypes_to_send_sales_invoice": "فواتير المبيعات (Sales Invoices)",
        "custom_doctypes_to_send_purchase_invoice": "فواتير المشتريات (Purchase Invoices)",
        "Doctypes to Send": "الفرص الواردة (Opportunities)",
        "Doctypes to Send": "الفرص الصادر (Opportunities)",
        "custom_doctypes_opportinity": "المراسلات الواردة والصادرة (Opportunities)",
        "custom_contract_modification_note_logs": "ملاحق العقد (Contract Modifications)",
        "custom_doctypes_to_send_estimated_assay": "المقايسات التقديرية (Estimated Assays)",
        "custom_request_cert": "طلبات الشهادات (Certificate Requests)",
        "custom_payment_claim_logs": "المطالبات المالية (Payment Claims)",
        "custom_tax_status": "حالة الضرائب (Tax Status)",
        "custom_tax_letters": "خطابات ضريبية (Tax Letters)",
        "custom_tax_release_logs": "سجلات الإعفاء الضريبي (Tax Release Logs)",
        "custom_doctypes_to_send_hazarads": "المخاطر (Hazards)",
        "custom_extension_letter": "خطابات التمديد (Extension Letters)",
        "custom_contract_periods_entity": "فترات العقد (Contract Periods)",
        "custom_dues_payment_log": "سجل المستحقات (Dues Payment)",
        "custom_consultant_letters": "خطابات الاستشاري (Consultant Letters)",
        "custom_supplier_quotation": "عروض أسعار الموردين (Supplier Quotations)",
        "custom_doctypes_to_send_quotation": "عروض الأسعار (Quotations)",
        "custom_doctypes_to_send_offer_note": "مذكرات العروض (Offer Notes)",
        "custom_child_projects": "مشاريع فرعية (Child Projects)",
        "custom_exchange_items_letter": "خطابات تبادل الأصناف (Exchange Items Letters)",
        "custom_bg_note": "ملاحظات الضمان (BG Notes)",
    }
    
    # Class-level cached LLM instance for SQL Agent (created once, reused)
    _cached_llm = None
    _cached_llm_provider = None

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
        """Execute SQL query using LangChain SQL Agent if available, otherwise fallback"""
        
        # Check if we are in database mode
        from backend.config import DATA_SOURCE
        
        if DATA_SOURCE == "database":
             try:
                from backend.ai_agent.database_service import get_database
                from langchain_community.agent_toolkits import create_sql_agent
                from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
                from langchain_openai import ChatOpenAI
                try:
                    from langchain_ollama import OllamaLLM
                except ImportError:
                    from langchain_community.llms import Ollama as OllamaLLM
                from backend.config import AI_CONFIG
                
                from backend.ai_agent.database_service import get_restricted_db
                
                # Determine tables to include to prevent context overflow ("Chunk too big")
                tables_to_include = []
                
                # 1. Use tables from domain context (identified by Thinking Agent)
                if domain_context.get("tables"):
                    tables_to_include.extend(domain_context["tables"])
                    
                # 2. Add tables based on query keywords (using SUBTABLE_MAP)
                query_lower = query.lower()
                for keyword, mapped_tables in self.SUBTABLE_MAP.items():
                    if keyword in query_lower:
                        tables_to_include.extend(mapped_tables)
                
                # 3. If still empty, use a sensible default set of core tables
                if not tables_to_include:
                     tables_to_include = [
                         "Operations",        # Projects
                         "EntityInvoices",    # Sales
                         "Contracts",         # Contracts
                         "PaymentOrders",     # Purchases
                         "AssignmentOrders",  # Sales Orders
                         "Users",             # Users
                         "Roles",             # User roles
                         "Permissions",       # Permissions
                         "Entities",          # Customers/Suppliers
                         "LookupItems",       # Lookup values
                     ]
                
                # 4. Auto-include related tables when relevant ones are present
                RELATED_TABLES = {
                    "Users": ["Roles", "UserRoles", "RolePermissions", "Permissions"],
                    "Roles": ["Users", "RolePermissions", "Permissions"],
                    "Operations": ["OperationFiles", "OperationClauses", "OperationTimelines"],
                    "EntityInvoices": ["EntityInvoiceItems"],
                    "PaymentOrders": ["PaymentOrderClaims", "PaymentOrderInvoices"],
                    "Contracts": ["CompanyContracts"],
                }
                expanded = set(tables_to_include)
                for t in list(expanded):
                    if t in RELATED_TABLES:
                        expanded.update(RELATED_TABLES[t])
                tables_to_include = list(expanded)
                
                # Safety check: If list is still huge, limit it? 
                # (Unlikely with this logic, but good to know)
                
                logger.info(f"[PROCESSING AGENT] Restricting SQL Agent to tables: {tables_to_include}")
                
                # Get restricted database instance
                db = get_restricted_db(tables_to_include)
                if db:
                    logger.info("[PROCESSING AGENT] Using LangChain SQL Agent")
                    
                    # Get or create cached LLM instance (singleton)
                    current_provider = AI_CONFIG["model_provider"]
                    if ProcessingAgent._cached_llm is None or ProcessingAgent._cached_llm_provider != current_provider:
                        if current_provider == "openai":
                            ProcessingAgent._cached_llm = ChatOpenAI(
                                model=AI_CONFIG["openai_model"],
                                api_key=AI_CONFIG["openai_api_key"],
                                temperature=0
                            )
                        else:
                            ProcessingAgent._cached_llm = OllamaLLM(
                                base_url=AI_CONFIG["ollama_base_url"],
                                model=AI_CONFIG["ollama_model"],
                                temperature=0
                            )
                        ProcessingAgent._cached_llm_provider = current_provider
                        logger.info(f"[PROCESSING AGENT] Created cached LLM ({current_provider})")
                    
                    llm = ProcessingAgent._cached_llm
                    
                    # Create SQL Agent with strict double-quoting rules
                    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
                    
                    schema_info = ""
                    try:
                        # Pre-fetch the exact schema string the agent usually wastes iterations acquiring
                        schema_info = db.get_table_info()
                    except Exception as e:
                        logger.warning(f"[PROCESSING AGENT] Could not fetch schema info directly: {e}")

                    sql_agent_prefix = f"""You are an agent designed to interact with a PostgreSQL database.

Here is the exact schema information for the tables you are allowed to query. Review it carefully before answering.
<schema>
{schema_info}
</schema>

CRITICAL RULE - DOUBLE QUOTES ON EVERY IDENTIFIER:
This PostgreSQL database has case-sensitive table and column names.
You MUST wrap EVERY table name and EVERY column name in double quotes.

CORRECT:   SELECT "Username", "RoleId" FROM "Users" WHERE "IsActive" = true
CORRECT:   SELECT U."Username", R."RoleName" FROM "Users" U JOIN "Roles" R ON U."RoleId" = R."Id"
INCORRECT: SELECT Username FROM Users  -- THIS WILL FAIL!
INCORRECT: SELECT * FROM Roles         -- THIS WILL FAIL!

ALWAYS use double quotes. NEVER write a query without double quotes around identifiers.
If you get an 'UndefinedTable' or 'UndefinedColumn' error, it means you forgot double quotes.

Also limit your results with LIMIT 50 unless asked for all rows.

IMPORTANT GUIDELINES FOR SPEED:
1. DO NOT use the sql_db_list_tables tool. You already know which tables exist.
2. DO NOT use the sql_db_schema tool unless absolutely necessary.
3. Write your SELECT query immediately and execute it using sql_db_query."""

                    agent_executor = create_sql_agent(
                        llm=llm,
                        toolkit=toolkit,
                        verbose=True,
                        agent_type="zero-shot-react-description",
                        handle_parsing_errors=True,
                        max_iterations=8,
                        prefix=sql_agent_prefix
                    )
                    
                    # Execute
                    # Enhance query with domain context if needed
                    full_query = query
                    if domain_context.get("tables"):
                        full_query += f" (Focus on tables: {', '.join(domain_context['tables'])})"
                        
                    response = await agent_executor.ainvoke(full_query)
                    result_text = response.get("output", "")
                    
                    return {
                        "data": [{"result": result_text}], # SQL Agent returns text summary
                        "query": full_query,
                        "generated_query": "Generated by SQL Agent",
                        "summary": result_text
                    }
                    
             except Exception as e:
                logger.error(f"[PROCESSING AGENT] SQL Agent error: {e}")
                # Fallback to normal execution if agent fails
        
        # ... Rest of original implementation for JSON/Fallback ...
        tables = domain_context.get("tables", [])
        limit = parameters.get("limit", 50)
        order = parameters.get("order", "desc")
        
        if not tables:
            tables = ["Operations"]  # Default to Operations (projects) table
        
        query_lower = query.lower()
        
        # ====== STEP 1: CHECK FOR PROJECT OVERVIEW REQUEST ======
        overview_keywords_en = ["overview", "summary", "all data", "show project", "project data", "project details", "about project"]
        overview_keywords_ar = ["بيانات المشروع", "ملخص المشروع", "عرض المشروع", "تفاصيل المشروع", "نظرة عامة", "عن المشروع", "كل بيانات"]
        
        is_overview = (
            any(kw in query_lower for kw in overview_keywords_en) or
            any(kw in query for kw in overview_keywords_ar)
        )
        
        if is_overview and any(t.lower() in ["operations", "project_59"] for t in tables):
            logger.info("[PROCESSING AGENT] Project overview request detected")
            # Use SQL for project overview in database mode
            overview_sql = 'SELECT * FROM "Operations" LIMIT 50'
            data = self.adapter.execute_query(overview_sql)
            if data:
                return {"data": data, "query": overview_sql}
            return await self._get_project_overview()
        
        # ====== STEP 2: CHECK FOR SUBTABLE EXTRACTION ======
        # Use longer keywords first for better matching
        sorted_keywords = sorted(self.SUBTABLE_MAP.keys(), key=len, reverse=True)
        
        target_keys = None
        matched_keyword = None
        for keyword in sorted_keywords:
            if keyword in query_lower or keyword in query:
                target_keys = self.SUBTABLE_MAP[keyword]
                matched_keyword = keyword
                break
        
        if target_keys:
            logger.info(f"[PROCESSING AGENT] Subtable extraction: keyword='{matched_keyword}' → keys={target_keys}")
            return await self._extract_subtable_data(target_keys, limit, order)
        
        # ====== STEP 3: FALLBACK — GENERAL TABLE QUERY ======
        primary_table = tables[0]
        primary_table_lower = primary_table.lower()
        
        # Smart table selection (case-insensitive check)
        if "project" in query_lower or "مشروع" in query:
            # Check for Operations table
            proj_match = next((t for t in tables if t.lower() in ["operations"]), None)
            if proj_match:
                primary_table = proj_match
                primary_table_lower = primary_table.lower()
                
        elif "inventory" in query_lower:
            inv_match = next((t for t in tables if t.lower() in ["inventory", "items", "lookupitems"]), None)
            if inv_match:
                primary_table = inv_match
                primary_table_lower = primary_table.lower()
                
        elif "sales" in query_lower or "مبيعات" in query:
            sales_match = next((t for t in tables if t.lower() in ["sales", "entityinvoices", "invoices"]), None)
            if sales_match:
                primary_table = sales_match
                primary_table_lower = primary_table.lower()
        
        # Build query based on query type — ALL table names double-quoted for PostgreSQL
        qt = f'"' + primary_table + '"'  # quoted table name
        if "top" in query_lower or "ranking" in query_lower:
            if primary_table_lower == "operations":
                sql = f"SELECT * FROM {qt} LIMIT {limit}"
            elif primary_table_lower == "entityinvoices":
                sql = f"SELECT * FROM {qt} ORDER BY \"TotalAmount\" {order} LIMIT {limit}"
            else:
                sql = f"SELECT * FROM {qt} LIMIT {limit}"
        
        elif "total" in query_lower or "sum" in query_lower or "إجمالي" in query or "مجموع" in query:
             if primary_table_lower == "entityinvoices":
                 sql = f"SELECT SUM(\"TotalAmount\") as total FROM {qt}"
             else:
                 sql = f"SELECT * FROM {qt}"
        
        else:
            sql = f"SELECT * FROM {qt} LIMIT {limit}"
        
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
    
    async def _extract_subtable_data(
        self,
        target_tables: List[str],
        limit: int = 50,
        order: str = "desc"
    ) -> Dict[str, Any]:
        """Extract data from specific tables (formerly subtables)"""
        extracted_data = []
        
        for table in target_tables:
            # Query the table directly
            try:
                # Basic select query
                # If we have an OperationId, we could join, but for now we just list data
                if order == "desc":
                     # Try to find a logical sort column
                     # Generic sort isn't easy without known column, usually Id or Created
                     sql = f"SELECT * FROM \"{table}\" LIMIT {limit}"
                else:
                     sql = f"SELECT * FROM \"{table}\" LIMIT {limit}"
                
                logger.info(f"[PROCESSING AGENT] Querying subtable: {table}")
                data = self.adapter.execute_query(sql)
                
                if not data:
                    # Fallback to get_all if execute_query fails or returns empty (and not error)
                    data = self.adapter.get_all(table)[:limit]
                
                # Enrich data with source info
                for row in data:
                    row["_source_table"] = table
                    extracted_data.append(row)
                    
            except Exception as e:
                logger.error(f"[PROCESSING AGENT] Error querying table {table}: {e}")
        
        query_desc = f"Extracted data from {', '.join(target_tables)} ({len(extracted_data)} records)"
        
        return {
            "data": extracted_data[:limit],
            "query": query_desc
        }
    
    async def _get_project_overview(self) -> Dict[str, Any]:
        """Generate a structured project overview from Operations and EntityInvoices"""
        try:
            # Get recent operations (projects)
            sql_ops = 'SELECT "Id", "OperationName", "OperationDate", "StatusLookupItemId", "Created" FROM "Operations" ORDER BY "Created" DESC LIMIT 20'
            logger.info("[PROCESSING AGENT] Fetching Operations overview...")
            operations = self.adapter.execute_query(sql_ops)
            
            if not operations:
                # Fallback if execute_query returns empty but get_all works
                operations = self.adapter.get_all("Operations")[:20]
                
            if not operations:
                return {"data": [], "query": "Project overview - no operations found"}
            
            overview_records = []
            
            for op in operations:
                op_id = op.get("Id")
                op_name = op.get("OperationName") or f"Operation #{op_id}"
                op_date = op.get("OperationDate") or op.get("Created")
                status_id = op.get("StatusLookupItemId", "")
                
                # Calculate total sales from EntityInvoices for this operation
                total_sales = 0.0
                sales_count = 0
                
                if op_id:
                    # Handle UUID or Int ID properly in SQL
                    # Assuming Id is UUID/String based on typical ERP usage, need quotes
                    sql_sales = f'SELECT SUM("TotalAmount") as total, COUNT(*) as count FROM "EntityInvoices" WHERE "OperationId" = \'{op_id}\''
                    try:
                        sales_res = self.adapter.execute_query(sql_sales)
                        if sales_res and sales_res[0]:
                            row = sales_res[0]
                            total_sales = float(row.get("total") or 0)
                            sales_count = int(row.get("count") or 0)
                    except Exception as e:
                        logger.warning(f"[PROCESSING AGENT] Error fetching sales for op {op_id}: {e}")

                summary = {
                    "المشروع (Project)": op_name,
                    "التاريخ (Date)": str(op_date),
                    "الحالة (Status ID)": str(status_id),
                    "إجمالي الفواتير (Total Sales)": f"{total_sales:,.2f}",
                    "عدد الفواتير (Invoice Count)": str(sales_count)
                }
                
                # Check for other linked data if needed (e.g. Claims)
                # But keep it simple for now
                
                overview_records.append(summary)
            
            return {
                "data": overview_records,
                "query": "Recent Project Operations Overview (Standard SQL)"
            }
            
        except Exception as e:
            logger.error(f"[PROCESSING AGENT] Error generating overview: {e}")
            return {"data": [], "query": "Error generating overview", "error": str(e)}
    
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
        """Execute retrieval - uses hybrid RAG search (vector + keyword + table relevance) in database mode"""
        
        # Try enhanced RAG search first (database mode)
        from backend.config import DATA_SOURCE
        if DATA_SOURCE == "database":
            try:
                from backend.ai_agent.rag_search_service import get_rag_search_service
                rag_svc = get_rag_search_service()
                
                logger.info("[PROCESSING AGENT] Using hybrid RAG search (vector + keyword + table relevance)")
                rag_results = rag_svc.search(query, top_k=10)
                
                if rag_results:
                    results = []
                    for r in rag_results:
                        results.append({
                            "content": r.content,
                            "table": r.table_name,
                            "row_id": r.row_id,
                            "final_score": round(r.final_score, 4),
                            "vector_score": round(r.vector_score, 4),
                            "keyword_score": round(r.keyword_score, 4),
                            "_source": "hybrid_rag_search"
                        })
                    return {
                        "data": results,
                        "query": f"Hybrid RAG search: {query}"
                    }
                else:
                    logger.info("[PROCESSING AGENT] No RAG results, falling back to keyword search")
            except Exception as e:
                logger.warning(f"[PROCESSING AGENT] RAG search error: {e}, falling back to keyword")
        
        # Fallback: keyword-based search across database tables
        results = []
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        
        try:
            # Use database schema to get table list (not JSON_FILES)
            schema = self.adapter.get_schema()
            tables = [t for t in schema.keys() if t not in [
                "users", "agents", "conversations", "settings", "feedback",
                "embeddings", "__EFMigrationsHistory",
                "session_summaries", "cross_session_index", "user_preferences"
            ]]
            
            # Limit to a reasonable number of tables to avoid scanning everything
            search_tables = tables[:20]
            
            for table in search_tables:
                try:
                    data = self.adapter.get_all(table)
                except Exception:
                    continue
                
                for row in data[:100]:  # Limit rows per table for performance
                    row_str = ""
                    for k, v in row.items():
                        if isinstance(v, (str, int, float)):
                            row_str += f" {str(v).lower()}"
                    
                    match_count = sum(1 for term in query_terms if term in row_str)
                    
                    if match_count > 0:
                        result_row = {}
                        for k, v in row.items():
                            if isinstance(v, (str, int, float, bool)):
                                result_row[k] = v
                            elif isinstance(v, list):
                                result_row[k] = f"[{len(v)} items]"
                        result_row["_source"] = table
                        result_row["_relevance"] = match_count
                        results.append(result_row)
            
            results.sort(key=lambda x: x["_relevance"], reverse=True)
            
            return {
                "data": results[:10],
                "query": f"Search for: {', '.join(query_terms)}"
            }
            
        except Exception as e:
            logger.error(f"[PROCESSING AGENT] RAG Error: {e}")
            return {
                "data": [],
                "error": str(e),
                "query": "RAG Search Failed"
            }

