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
    
    # Bilingual keyword → subtable key mapping (English + Arabic)
    SUBTABLE_MAP = {
        # Bank Guarantees
        "cancel bank": ["custom_custom_doctypes_to_cancel_bank_guarantee"],
        "إلغاء ضمان": ["custom_custom_doctypes_to_cancel_bank_guarantee"],
        "bank guarantee": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
        "bank": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
        "guarantee": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
        "ضمان بنكي": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
        "ضمان": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
        "خطاب ضمان": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
        "بنك": ["custom_custom_doctypes_to_cancel_bank_guarantee", "custom_doctypes_to_send_bank_guarantee"],
        
        # Invoices
        "sales invoice": ["custom_doctypes_to_send_sales_invoice"],
        "فاتورة مبيعات": ["custom_doctypes_to_send_sales_invoice"],
        "فواتير المبيعات": ["custom_doctypes_to_send_sales_invoice"],
        "purchase invoice": ["custom_doctypes_to_send_purchase_invoice"],
        "فاتورة مشتريات": ["custom_doctypes_to_send_purchase_invoice"],
        "فواتير المشتريات": ["custom_doctypes_to_send_purchase_invoice"],
        "invoice": ["custom_doctypes_to_send_sales_invoice", "custom_doctypes_to_send_purchase_invoice"],
        "فاتورة": ["custom_doctypes_to_send_sales_invoice", "custom_doctypes_to_send_purchase_invoice"],
        "فواتير": ["custom_doctypes_to_send_sales_invoice", "custom_doctypes_to_send_purchase_invoice"],
        
        # Orders
        "sales order": ["custom_doctypes_to_send_sales_order"],
        "أمر بيع": ["custom_doctypes_to_send_sales_order"],
        "أوامر البيع": ["custom_doctypes_to_send_sales_order"],
        "purchase order": ["custom_doctypes_to_send_purchase_order"],
        "أمر شراء": ["custom_doctypes_to_send_purchase_order"],
        "أوامر الشراء": ["custom_doctypes_to_send_purchase_order"],
        "order": ["custom_doctypes_to_send_sales_order", "custom_doctypes_to_send_purchase_order"],
        "طلب": ["custom_doctypes_to_send_sales_order", "custom_doctypes_to_send_purchase_order"],
        "أمر توريد": ["custom_doctypes_to_send_sales_order"],
        "أوامر": ["custom_doctypes_to_send_sales_order", "custom_doctypes_to_send_purchase_order"],
        
        # Opportunities
        "opportunity": ["custom_doctypes_opportinity", "custom_doctypes_to_send_opportinity", "custom_tax_opporunity"],
        "فرصة": ["custom_doctypes_opportinity", "custom_doctypes_to_send_opportinity", "custom_tax_opporunity"],
        "فرص": ["custom_doctypes_opportinity", "custom_doctypes_to_send_opportinity", "custom_tax_opporunity"],
        "خطابات": ["custom_doctypes_opportinity", "custom_doctypes_to_send_opportinity"],
        "خطاب": ["custom_doctypes_opportinity", "custom_doctypes_to_send_opportinity"],
        "وارد": ["custom_doctypes_opportinity"],
        "صادر": ["custom_doctypes_opportinity"],
        
        # Quotations
        "quotation": ["custom_doctypes_to_send_quotation", "custom_supplier_quotation"],
        "عرض سعر": ["custom_doctypes_to_send_quotation", "custom_supplier_quotation"],
        "عرض أسعار": ["custom_doctypes_to_send_quotation", "custom_supplier_quotation"],
        "عروض": ["custom_doctypes_to_send_quotation", "custom_supplier_quotation"],
        
        # Offer Notes
        "offer": ["custom_doctypes_to_send_offer_note"],
        "عرض": ["custom_doctypes_to_send_offer_note"],
        
        # Contract Modifications
        "contract": ["custom_contract_modification_note_logs"],
        "modification": ["custom_contract_modification_note_logs"],
        "عقد": ["custom_contract_modification_note_logs"],
        "تعديل عقد": ["custom_contract_modification_note_logs"],
        "تعديل": ["custom_contract_modification_note_logs"],
        "ملحق": ["custom_contract_modification_note_logs"],
        
        # Estimated Assay (Quotation Estimates)
        "assay": ["custom_doctypes_to_send_estimated_assay"],
        "estimated": ["custom_doctypes_to_send_estimated_assay"],
        "مقايسة": ["custom_doctypes_to_send_estimated_assay"],
        "مقايسات": ["custom_doctypes_to_send_estimated_assay"],
        "تقديرية": ["custom_doctypes_to_send_estimated_assay"],
        
        # Certificates
        "certificate": ["custom_request_cert"],
        "شهادة": ["custom_request_cert"],
        "شهادات": ["custom_request_cert"],
        
        # Payment Claims
        "claim": ["custom_payment_claim_logs"],
        "payment": ["custom_payment_claim_logs"],
        "مطالبة": ["custom_payment_claim_logs"],
        "مطالبات": ["custom_payment_claim_logs"],
        "دفع": ["custom_payment_claim_logs"],
        "مستخلص": ["custom_payment_claim_logs"],
        
        # Tax
        "tax": ["custom_tax_status", "custom_tax_opporunity", "custom_tax_letters"],
        "ضريبة": ["custom_tax_status", "custom_tax_opporunity", "custom_tax_letters"],
        "ضرائب": ["custom_tax_status", "custom_tax_opporunity", "custom_tax_letters"],
        "إعفاء": ["custom_tax_release_logs"],
        
        # Hazards
        "hazard": ["custom_doctypes_to_send_hazarads"],
        "risk": ["custom_doctypes_to_send_hazarads"],
        "مخاطر": ["custom_doctypes_to_send_hazarads"],
        
        # Extension Letters
        "extension": ["custom_extension_letter"],
        "تمديد": ["custom_extension_letter"],
        "مد مدة": ["custom_extension_letter"],
        
        # Contract Periods
        "period": ["custom_contract_periods_entity"],
        "فترة": ["custom_contract_periods_entity"],
        "فترات": ["custom_contract_periods_entity"],
        "مدة العقد": ["custom_contract_periods_entity"],
        
        # Dues Payment
        "dues": ["custom_dues_payment_log"],
        "مستحقات": ["custom_dues_payment_log"],
        
        # Consultant Letters
        "consultant": ["custom_consultant_letters"],
        "استشاري": ["custom_consultant_letters"],

        "Letter": ["custom_doctypes_to_send_opportinity"],
        "الخطابات": ["custom_doctypes_to_send_opportinity"],    
        "خطاب": ["custom_doctypes_to_send_opportinity"],

        
        "مطالبة صرف": ["custom_payment_claim_logs"],
        "claim": ["custom_payment_claim_logs"], 
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
        """Execute SQL-like query on data with deep nested extraction"""
        tables = domain_context.get("tables", [])
        limit = parameters.get("limit", 50)
        order = parameters.get("order", "desc")
        
        if not tables:
            tables = ["project_59"]  # Default to project data
        
        query_lower = query.lower()
        
        # ====== STEP 1: CHECK FOR PROJECT OVERVIEW REQUEST ======
        overview_keywords_en = ["overview", "summary", "all data", "show project", "project data", "project details", "about project"]
        overview_keywords_ar = ["بيانات المشروع", "ملخص المشروع", "عرض المشروع", "تفاصيل المشروع", "نظرة عامة", "عن المشروع", "كل بيانات"]
        
        is_overview = (
            any(kw in query_lower for kw in overview_keywords_en) or
            any(kw in query for kw in overview_keywords_ar)
        )
        
        if is_overview and "project_59" in tables:
            logger.info("[PROCESSING AGENT] Project overview request detected")
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
        
        # Smart table selection
        if "project" in query_lower or "مشروع" in query:
            if "project_59" in tables:
                primary_table = "project_59"
        elif "inventory" in query_lower and "inventory" in tables:
            primary_table = "inventory"
        elif "sales" in query_lower or "مبيعات" in query:
            if "sales" in tables and self.adapter.get_all("sales"):
                primary_table = "sales"
            elif "project_59" in tables:
                primary_table = "project_59"
        
        # Build query based on query type
        if "top" in query_lower or "ranking" in query_lower or "project" in query_lower or "مشروع" in query:
            if primary_table == "project_59":
                sql = f"SELECT * FROM project_59 ORDER BY total_sales_amount {order} LIMIT {limit}"
            elif primary_table == "sales":
                sql = f"SELECT * FROM sales ORDER BY amount {order} LIMIT {limit}"
            elif primary_table == "inventory":
                sql = f"SELECT * FROM inventory ORDER BY quantity {order} LIMIT {limit}"
            else:
                sql = f"SELECT * FROM {primary_table} LIMIT {limit}"
        
        elif "total" in query_lower or "sum" in query_lower or "إجمالي" in query or "مجموع" in query:
            sql = f"SELECT * FROM {primary_table}"
        
        else:
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
    
    async def _extract_subtable_data(
        self,
        target_keys: List[str],
        limit: int = 50,
        order: str = "desc"
    ) -> Dict[str, Any]:
        """Extract nested subtable data from project_59 with rich context"""
        project_data = self.adapter.get_all("project_59")
        extracted_data = []
        source_labels = []
        
        for proj in project_data:
            for key in target_keys:
                if key in proj and isinstance(proj[key], list):
                    label = self.SUBTABLE_LABELS.get(key, key)
                    source_labels.append(label)
                    items = proj[key]
                    for item in items:
                        if isinstance(item, dict):
                            # Add context metadata
                            enriched = {
                                "_source_table": label,
                                "_project_name": proj.get("project_name", ""),
                                "_project_id": proj.get("name", ""),
                            }
                            # Add the most useful fields first for readability
                            for field in ["reference_type", "reference_name", "doc_details", "totals", "customer", "idx"]:
                                if field in item:
                                    enriched[field] = item[field]
                            # Add remaining fields
                            for k, v in item.items():
                                if k not in enriched and k not in ("parent", "parentfield", "parenttype", "doctype", "docstatus", "owner", "creation", "modified", "modified_by"):
                                    enriched[k] = v
                            extracted_data.append(enriched)
        
        # Sort by totals or idx
        if extracted_data:
            try:
                extracted_data.sort(
                    key=lambda x: float(x.get("totals", x.get("idx", 0)) or 0),
                    reverse=(order == "desc")
                )
            except (ValueError, TypeError):
                pass
        
        unique_labels = list(dict.fromkeys(source_labels))
        query_desc = f"Extracted {', '.join(unique_labels)} ({len(extracted_data)} records)"
        
        return {
            "data": extracted_data[:limit],
            "query": query_desc
        }
    
    async def _get_project_overview(self) -> Dict[str, Any]:
        """Generate a structured project overview with subtable counts"""
        project_data = self.adapter.get_all("project_59")
        
        if not project_data:
            return {"data": [], "query": "Project overview - no data found"}
        
        overview_records = []
        
        for proj in project_data:
            # Build summary with top-level fields
            summary = {
                "المشروع (Project)": proj.get("name", ""),
                "اسم المشروع (Project Name)": proj.get("project_name", ""),
                "العميل (Customer)": proj.get("customer", ""),
                "الشركة (Company)": proj.get("company", ""),
                "الحالة (Status)": proj.get("status", ""),
                "حالة المشروع (PR Status)": proj.get("custom_pr_status", ""),
                "نوع المشروع (Type)": proj.get("project_type", ""),
                "نوع التعاقد (Contract Type)": proj.get("custom_type_of_contracts", ""),
                "إجمالي المبيعات (Total Sales)": f"{proj.get('total_sales_amount', 0):,.0f}",
                "إجمالي المشتريات (Total Purchase Cost)": f"{proj.get('total_purchase_cost', 0):,.0f}",
                "إجمالي الفواتير (Total Billed)": f"{proj.get('total_billed_amount', 0):,.0f}",
                "هامش الربح (Gross Margin)": f"{proj.get('gross_margin', 0):,.0f}",
                "نسبة الربحية (Profitability %)": f"{proj.get('custom_project_profitability', 0):.2f}%",
                "المورد المعتمد (Accepted Supplier)": proj.get("custom_accepted_supplier", ""),
                "السنة المالية (Fiscal Year)": proj.get("custom_project_fiscal_year", ""),
                "الأولوية (Priority)": proj.get("priority", ""),
            }
            
            # Count nested subtables
            subtable_summary = {}
            for key, label in self.SUBTABLE_LABELS.items():
                if key in proj and isinstance(proj[key], list) and len(proj[key]) > 0:
                    count = len(proj[key])
                    # Calculate total if items have 'totals' field
                    items = proj[key]
                    total_value = sum(
                        float(item.get("totals", 0) or 0) 
                        for item in items 
                        if isinstance(item, dict)
                    )
                    if total_value > 0:
                        subtable_summary[label] = f"{count} records (Total: {total_value:,.0f})"
                    else:
                        subtable_summary[label] = f"{count} records"
            
            summary["البيانات الفرعية (Sub-tables)"] = subtable_summary
            overview_records.append(summary)
        
        return {
            "data": overview_records,
            "query": "Project 59 - Full Overview"
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
        """Execute text-based retrieval across all data including nested subtables"""
        results = []
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        
        try:
            from backend.config import JSON_FILES
            tables = list(JSON_FILES.keys())
            
            for table in tables:
                if table in ["users", "agents", "conversations", "settings"]:
                    continue
                
                data = self.adapter.get_all(table)
                
                for row in data:
                    # Search top-level fields
                    row_str = ""
                    for k, v in row.items():
                        if isinstance(v, (str, int, float)):
                            row_str += f" {str(v).lower()}"
                        elif isinstance(v, list):
                            # Search inside nested arrays too
                            for item in v:
                                if isinstance(item, dict):
                                    for ik, iv in item.items():
                                        if isinstance(iv, (str, int, float)):
                                            row_str += f" {str(iv).lower()}"
                    
                    match_count = sum(1 for term in query_terms if term in row_str)
                    
                    if match_count > 0:
                        result_row = {}
                        # Only include readable fields
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
