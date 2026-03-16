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
        """Execute SQL query.
        
        Priority:
          STEP 0: Direct view query (vw_Customer_Project_Invoices / vw_Supplier_Project_Invoices)
          STEP 1: LangChain SQL Agent (for complex queries or non-view answers)
          STEP 2: Fallback direct SQL / JSON
        """
        from backend.config import DATA_SOURCE

        # ── STEP 0: VIEW-FIRST EXECUTION ──────────────────────────────────────
        use_views = domain_context.get("use_views", False)
        target_views = domain_context.get("target_views", [])
        matching_report = domain_context.get("matching_report")

        if DATA_SOURCE == "database" and use_views and target_views:
            try:
                from backend.ai_agent.view_query_service import get_view_query_service
                view_svc = get_view_query_service()

                limit = parameters.get("limit", 50)
                query_type = domain_context.get("primary_domain", "general")
                all_results = []

                for view_name in target_views:
                    # Determine if aggregation is needed
                    agg = None
                    query_lower = query.lower()
                    if any(kw in query_lower or kw in query for kw in [
                        "total", "sum", "إجمالي", "مجموع", "count", "عدد"
                    ]):
                        agg = "sum"
                    elif any(kw in query_lower or kw in query for kw in [
                        "count", "how many", "كم"
                    ]):
                        agg = "count"

                    sql = view_svc.build_view_sql(
                        view_name=view_name,
                        limit=limit,
                        aggregate=agg
                    )
                    logger.info(f"[PROCESSING AGENT] ⭐ View-first query → {view_name}: {sql}")
                    rows = view_svc.execute_view_query(view_name, sql)
                    for row in rows:
                        row["_source_view"] = view_name
                        all_results.append(row)

                if all_results:
                    hint = f"Data sourced from master view(s): {', '.join(target_views)}"
                    if matching_report:
                        hint += f" | Few-shot template: {matching_report}"
                    logger.info(f"[PROCESSING AGENT] ✅ View-first returned {len(all_results)} rows")
                    return {
                        "data": all_results,
                        "query": f"SELECT * FROM {' + '.join(target_views)} (view-first)",
                        "generated_query": sql,
                        "source": "view_first",
                        "summary": hint
                    }
                else:
                    logger.warning("[PROCESSING AGENT] View query returned no rows, falling through to SQL Agent")

            except Exception as e:
                logger.warning(f"[PROCESSING AGENT] View-first execution failed: {e}, falling through")

        # ── STEP 1: LANGCHAIN SQL AGENT ────────────────────────────────────────
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

                # Tables to include — views are always present
                tables_to_include = [
                    "vw_Customer_Project_Invoices",
                    "vw_Supplier_Project_Invoices"
                ]

                # 1. Target views from domain context (highest priority)
                if domain_context.get("target_views"):
                    tables_to_include.extend(domain_context["target_views"])

                # 2. Additional tables from domain context
                if domain_context.get("tables"):
                    for t in domain_context["tables"]:
                        if t not in tables_to_include:
                            tables_to_include.append(t)

                # 3. SUBTABLE_MAP keyword matching
                query_lower = query.lower()
                for keyword, mapped_tables in self.SUBTABLE_MAP.items():
                    if keyword in query_lower:
                        for t in mapped_tables:
                            if t not in tables_to_include:
                                tables_to_include.append(t)

                # 4. Default fallback — views + core tables
                if not tables_to_include:
                    tables_to_include = [
                        "vw_Customer_Project_Invoices",
                        "vw_Supplier_Project_Invoices",
                        "Operations",
                        "EntityInvoices",
                        "Entities",
                        "PaymentOrders",
                        "LookupItems",
                    ]

                # 5. Auto-include related tables when relevant
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

                logger.info(f"[PROCESSING AGENT] SQL Agent tables: {tables_to_include}")
                db = get_restricted_db(tables_to_include)
                if db:
                    logger.info("[PROCESSING AGENT] Using LangChain SQL Agent")

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

                    llm = ProcessingAgent._cached_llm

                    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
                    schema_info = ""
                    try:
                        raw_schema = db.get_table_info()
                        # Quadruple-escape curly braces:
                        # create_sql_agent calls prefix.format(dialect=..., top_k=...) which consumes one layer.
                        # Then PromptTemplate.from_template(template) consumes the second layer.
                        # Net result: {{{{ -> {{ -> {  (literal, safe)
                        schema_info = raw_schema.replace("{", "{{{{").replace("}", "}}}}") 
                    except Exception as e:
                        logger.warning(f"[PROCESSING AGENT] Could not fetch schema info: {e}")

                    # Inject ALL relevant few-shot report templates (multi-report, labeled)
                    few_shot_section = ""
                    try:
                        from backend.ai_agent.view_query_service import get_view_query_service
                        view_svc = get_view_query_service()
                        raw_few_shot = view_svc.build_few_shot_block(query, max_chars_per_report=800)
                        if raw_few_shot:
                            # Same quadruple-escape so JSON in SQL examples doesn't crash the prompt formatter
                            few_shot_section = raw_few_shot.replace("{", "{{{{").replace("}", "}}}}") 
                            matched_labels = [r[1] for r in view_svc.get_matching_reports(query, top_k=3)]
                            logger.info(f"[PROCESSING AGENT] 📋 Injected few-shot reports: {matched_labels}")
                    except Exception as e:
                        logger.warning(f"[PROCESSING AGENT] Could not build few-shot block: {e}")

                    # Retrieve safety guard constraints if present
                    safety = thinking_result.get("safety_guard", {}) if "thinking_result" in locals() else {}
                    entity_filter = safety.get("entity_filter")
                    safety_level = safety.get("safety_level", "SAFE")
                    
                    filter_instruction = ""
                    if entity_filter:
                        filter_instruction = f"""
CRITICAL RULE — FILTER REQUIRED:
The user is specifically asking about "{entity_filter}".
You MUST include a WHERE clause filtering by this entity using ILIKE or similar matching.
Example: WHERE "EntityName" ILIKE '%{entity_filter}%' OR "ClientName" ILIKE '%{entity_filter}%' 
If you fail to include this filter, you will scan too much data and fail.
"""

                    sql_agent_prefix = f"""You are an agent designed to interact with a PostgreSQL database.

CRITICAL RULE — ALWAYS USE VIEWS FIRST:
The database has 2 master views that already contain pre-joined, clean data:
  1. "vw_Customer_Project_Invoices" — Use for revenue, client invoices, project status
  2. "vw_Supplier_Project_Invoices" — Use for supplier costs, procurement invoices

ALWAYS prefer querying these views over raw tables whenever possible.
{few_shot_section}
Here is the exact schema information:
<schema>
{schema_info}
</schema>

CRITICAL RULE — DOUBLE QUOTES ON EVERY IDENTIFIER:
CORRECT:   SELECT "InvoiceNumber", "TotalAfterDiscountInvoice" FROM "vw_Customer_Project_Invoices" LIMIT 50
INCORRECT: SELECT InvoiceNumber FROM vw_Customer_Project_Invoices  -- WILL FAIL!

IMPORTANT GUIDELINES FOR SPEED:
1. DO NOT use sql_db_list_tables. You already know which tables/views exist.
2. DO NOT use sql_db_schema unless absolutely necessary.
3. Write your SELECT query immediately using sql_db_query. Execute it once and return the result.
4. DO NOT use sql_db_query_checker. Skip the checker and run the query directly.
5. Always LIMIT results to 50 unless asked otherwise.
6. Do NOT repeat the same action or tool call more than once.
{filter_instruction}"""

                    agent_executor = create_sql_agent(
                        llm=llm,
                        toolkit=toolkit,
                        verbose=True,
                        agent_type="zero-shot-react-description",
                        handle_parsing_errors=True,
                        max_iterations=5,          # small model loops if more
                        max_execution_time=90,     # hard wall: 90 seconds
                        prefix=sql_agent_prefix
                    )

                    full_query = query
                    if domain_context.get("target_views"):
                        full_query += f" (Prefer views: {', '.join(domain_context['target_views'])})"

                    import asyncio
                    try:
                        response = await asyncio.wait_for(
                            agent_executor.ainvoke(full_query),
                            timeout=120  # absolute hard cap at 2 minutes
                        )
                    except asyncio.TimeoutError:
                        logger.error("[PROCESSING AGENT] SQL Agent timed out after 120s")
                        raise RuntimeError("SQL Agent exceeded the 2-minute time limit. Please rephrase the query to be more specific.")
                    result_text = response.get("output", "")

                    return {
                        "data": [{"result": result_text}],
                        "query": full_query,
                        "generated_query": "Generated by SQL Agent",
                        "summary": result_text
                    }

             except Exception as e:
                import traceback
                logger.error(f"[PROCESSING AGENT] SQL Agent error: {e}")
                logger.error(f"[PROCESSING AGENT] Traceback: {traceback.format_exc()}")

        
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
        
        logger.info(f"[PROCESSING AGENT] Generated Fallback SQL: {sql}")
        
        # ── PHASE 5: AST SQL SAFETY GUARD ──
        from backend.ai_agent.sql_safety_guard import SqlSafetyGuard
        guard_result = SqlSafetyGuard.validate_and_patch(sql, max_limit=limit)
        
        if not guard_result["safe"]:
            logger.warning(f"[PROCESSING AGENT] SQL blocked by AST Guard: {guard_result['error']}")
            return {
                "data": [],
                "query": sql,
                "error": guard_result["error"]
            }
            
        safe_sql = guard_result["sql"]
        logger.info(f"[PROCESSING AGENT] Executing Patched AST SQL: {safe_sql}")
        
        # Execute safeguarded query on data adapter
        data = self.adapter.execute_query(safe_sql)
        
        # If no SQL results, try direct table access (read-only, naturally safe)
        if not data:
            data = self.adapter.get_all(primary_table)[:limit]
        
        return {
            "data": data,
            "query": safe_sql
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

