"""
ViewQueryService — Core Data Routing Layer
==========================================
This service is the FIRST step in every data query. It:
  1. Checks if user query can be answered by the 2 master views
  2. Loads few-shot SQL report templates from data/reports/ for LLM hints
  3. Executes direct view queries — no complex joins needed

Priority:
  1st: vw_Customer_Project_Invoices  (Revenue / Client Invoices / Project Status)
  2nd: vw_Supplier_Project_Invoices  (Costs / Supplier Invoices / Contracts)
  3rd: Raw DB tables (anything not covered above)
"""
import os
import glob
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── View column metadata ──────────────────────────────────────────────────────
VIEW_SCHEMAS = {
    "vw_Customer_Project_Invoices": {
        "description": (
            "MASTER REVENUE VIEW. Contains all client invoices linked to projects. "
            "Use for: revenue, client billing, invoice totals, project financial status, "
            "collection rates, paid vs unpaid invoices, entity/client info."
        ),
        "columns": [
            "InvoiceNumber", "InvoiceDate", "InvoiceDeliveryDate",
            "IsPaidInvoice", "TotalAmountInvoice", "TotalAfterDiscountInvoice",
            "TotalQuantityInvoice", "EntityName", "EntityAR",
            "EntityTaxRegistrationNumber", "EntityType", "EntityTypeAR",
            "ProjectNumber", "ProjectName", "ProjectNameAR", "ProjectDate",
            "ProjectStatus", "ProjectStatusAR", "ProjectType", "ProjectTypeAR",
            "IsPostponedProject", "DepartmentNameAR", "DepartmentNameEN"
        ],
        "key_amount_col": "TotalAfterDiscountInvoice",
        "key_date_col": "InvoiceDate",
        "key_name_col": "EntityName",
        "key_project_col": "ProjectName",
    },
    "vw_Supplier_Project_Invoices": {
        "description": (
            "MASTER COST VIEW. Contains all supplier/subcontractor invoices linked to projects. "
            "Use for: supplier costs, procurement costs, contract details, "
            "company invoice totals, fiscal year, tender types."
        ),
        "columns": [
            "SupplierInvoiceNumber", "SupplierTaxRegistrationNumber",
            "TotalPaidAmount", "TotalQuantity", "DiscountValue", "TotalPrice",
            "SupplierName", "SupplierNameAR", "SupplierType", "SupplierTypeAR",
            "FiscalYear", "TenderTypeNameAR", "ContractTypeNameAR",
            "ContractNumberWithEntity", "ContractDateWithEntity", "ReceiptDate",
            "ProjectNumber", "ProjectName", "ProjectDate", "ProjectIsPostponed",
            "ProjectStatus", "ProjectStatusAR", "ProjectType", "ProjectTypeAR",
            "DepartmentNameAR", "DepartmentNameEN"
        ],
        "key_amount_col": "TotalPrice",
        "key_date_col": "ProjectDate",
        "key_name_col": "SupplierName",
        "key_project_col": "ProjectName",
    }
}

# ── Keyword → view routing (English + Arabic) ────────────────────────────────
VIEW_ROUTING = {
    "vw_Customer_Project_Invoices": [
        # English
        "revenue", "client invoice", "customer invoice", "invoice",
        "billing", "invoiced", "paid", "unpaid", "collection", "income",
        "sales", "client", "customer", "entity", "collection rate",
        "project revenue", "project invoice", "total amount",
        # Arabic
        "فاتورة", "فواتير", "ايراد", "ايرادات", "مبيعات",
        "عميل", "عملاء", "تحصيل", "مدفوع", "مستحق",
        "إجمالي الفواتير", "فاتورة المشروع", "مبلغ الفاتورة",
    ],
    "vw_Supplier_Project_Invoices": [
        # English
        "cost", "supplier", "supplier invoice", "subcontractor", "vendor",
        "company invoice", "procurement", "tender", "contract cost",
        "fiscal year", "paid amount", "supplier cost", "purchase",
        # Arabic
        "تكلفة", "تكاليف", "مورد", "موردين", "مشتريات",
        "فاتورة مورد", "شركة", "عطاء", "مناقصة", "تكاليف المشروع",
        "اجمالي المشتريات",
    ],
    "both": [  # triggers both views (for P&L / profit comparisons)
        "profit", "margin", "pnl", "p&l", "revenue vs cost",
        "cost vs revenue", "net", "yield", "financial",
        "ربح", "هامش", "ارباح", "ربحية", "مالي",
    ]
}

# ── Report template tags (loaded from sql files) ──────────────────────────────
REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "reports"
)


class ViewQueryService:
    """
    Routes user queries to core views OR few-shot reports before
    hitting raw database schema. This is the FIRST layer of data retrieval.
    """
    _instance: Optional["ViewQueryService"] = None

    @classmethod
    def get_instance(cls) -> "ViewQueryService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._reports: Dict[str, str] = {}   # filename → SQL content
        self._report_tags: Dict[str, List[str]] = {}  # filename → tag list
        self._load_reports()

    def _load_reports(self):
        """Load all .sql report files from data/reports/ at startup."""
        try:
            sql_files = glob.glob(os.path.join(REPORTS_DIR, "*.sql"))
            for filepath in sql_files:
                fname = os.path.basename(filepath)
                if fname.startswith("00_"):
                    continue  # skip core views DDL
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                self._reports[fname] = content

                # Extract FEW-SHOT TAGS from comment header
                tags = []
                for line in content.splitlines():
                    if "FEW-SHOT TAGS:" in line:
                        raw = line.split("FEW-SHOT TAGS:")[-1].strip().rstrip("=").strip()
                        tags = [t.strip() for t in raw.split(",") if t.strip()]
                        break
                self._report_tags[fname] = tags

            logger.info(f"[ViewQueryService] Loaded {len(self._reports)} SQL report templates")
        except Exception as e:
            logger.error(f"[ViewQueryService] Error loading reports: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def can_answer_from_views(self, query: str) -> Tuple[bool, List[str]]:
        """
        Returns (True, [view_names]) if the query can be answered from the core views.
        Returns (False, []) if this requires raw table access.
        """
        query_lower = query.lower()
        matched_views = set()

        for view_name, keywords in VIEW_ROUTING.items():
            for kw in keywords:
                if kw in query_lower or kw in query:
                    if view_name == "both":
                        matched_views.add("vw_Customer_Project_Invoices")
                        matched_views.add("vw_Supplier_Project_Invoices")
                    else:
                        matched_views.add(view_name)
                    break

        # Always include customer view if project/operation detected (most common query)
        project_keywords = ["project", "operation", "مشروع", "مشاريع", "عملية", "عمليات"]
        for kw in project_keywords:
            if kw in query_lower or kw in query:
                matched_views.add("vw_Customer_Project_Invoices")
                break

        if matched_views:
            return True, list(matched_views)
        return False, []

    def build_view_sql(
        self,
        view_name: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        order_by: Optional[str] = None,
        aggregate: Optional[str] = None,  # "sum", "count", "avg"
    ) -> str:
        """
        Build a clean SELECT query against a core view.
        No joins needed — the view already contains everything.
        """
        schema = VIEW_SCHEMAS.get(view_name, {})
        amount_col = schema.get("key_amount_col", "")
        date_col = schema.get("key_date_col", "")

        # Build SELECT
        if aggregate == "sum" and amount_col:
            select_clause = f'SUM("{amount_col}") AS "TotalValue", COUNT(*) AS "RecordCount"'
        elif aggregate == "count":
            select_clause = 'COUNT(*) AS "RecordCount"'
        else:
            select_clause = "*"

        # Build WHERE
        where_parts = []
        if filters:
            for col, val in filters.items():
                if isinstance(val, str):
                    where_parts.append(f'"{col}" ILIKE \'%{val}%\'')
                elif isinstance(val, bool):
                    where_parts.append(f'"{col}" = {str(val).lower()}')
                else:
                    where_parts.append(f'"{col}" = {val}')

        where_clause = f"WHERE {' AND '.join(where_parts)}" if where_parts else ""

        # Build ORDER BY
        if order_by:
            order_clause = f'ORDER BY "{order_by}" DESC'
        elif amount_col and not aggregate:
            order_clause = f'ORDER BY "{amount_col}" DESC NULLS LAST'
        else:
            order_clause = ""

        # Assemble
        limit_clause = f"LIMIT {limit}" if not aggregate else ""

        sql = f'SELECT {select_clause} FROM "{view_name}" {where_clause} {order_clause} {limit_clause}'
        return sql.strip()

    def get_view_schema_description(self) -> str:
        """
        Returns a formatted string of view schemas to inject into LLM system prompt.
        """
        lines = [
            "## ⭐ PRIORITY DATA SOURCES — ALWAYS USE THESE FIRST",
            "",
            "These are pre-built master views. Query them directly — no raw table joins needed.",
            "",
        ]
        for view_name, schema in VIEW_SCHEMAS.items():
            cols_preview = ", ".join(schema["columns"][:12]) + " ..."
            lines.append(f"### `{view_name}`")
            lines.append(f"**Purpose**: {schema['description']}")
            lines.append(f"**Key Columns**: {cols_preview}")
            lines.append(f"**Amount Column**: `{schema['key_amount_col']}`")
            lines.append(f"**Date Column**: `{schema['key_date_col']}`")
            lines.append("")
        return "\n".join(lines)

    # Human-readable names for each report file (used as section labels in LLM prompt)
    REPORT_LABELS = {
        "01_executive_dashboard.sql":    "Executive Dashboard — Revenue & Entity Overview",
        "02_cash_flow_liquidity.sql":    "Cash Flow & Liquidity — Monthly Collections",
        "03_budget_variance.sql":        "Budget Variance — Billed vs Contracted",
        "04_departmental_yield.sql":     "Departmental Yield — Revenue & Cost by Department",
        "05_project_lifecycle_tracker.sql": "Project Lifecycle Tracker — Import to Invoice",
        "06_operation_pnl.sql":          "Operation P&L — Revenue vs Supplier Costs",
        "07_revenue_bottlenecks.sql":    "Revenue Bottlenecks — Pipeline Stage Analysis",
    }

    def get_matching_reports(self, query: str, top_k: int = 3) -> List[Tuple[str, str, str]]:
        """
        Returns list of (filename, label, sql_content) for ALL relevant reports,
        sorted by relevance score descending. Returns up to top_k matches.
        If no tags match, returns top_k reports generically (catch-all).
        """
        query_lower = query.lower()
        scored = []

        for fname, tags in self._report_tags.items():
            score = sum(1 for tag in tags if tag.lower() in query_lower or tag.lower() in query)
            scored.append((score, fname))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, fname in scored[:top_k]:
            label = self.REPORT_LABELS.get(fname, fname.replace("_", " ").replace(".sql", "").title())
            results.append((fname, label, self._reports.get(fname, "")))

        return results

    def get_matching_report(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Backwards-compatible: returns (filename, sql_content) for the top match.
        """
        matches = self.get_matching_reports(query, top_k=1)
        if matches:
            fname, label, sql = matches[0]
            return fname, sql
        return None

    def build_few_shot_block(self, query: str, max_chars_per_report: int = 800) -> str:
        """
        Build the complete few-shot section to inject into the SQL agent prefix.
        Includes ALL matching reports with human-readable section labels.
        Each report is truncated to max_chars_per_report to stay within LLM context.
        """
        matches = self.get_matching_reports(query, top_k=3)
        if not matches:
            return ""

        lines = [
            "",
            "=" * 60,
            "FEW-SHOT REFERENCE SQL REPORTS (use these structures as your guide):",
            "These are verified SQL patterns built on the master views.",
            "=" * 60,
        ]
        for i, (fname, label, sql) in enumerate(matches, 1):
            snippet = sql[:max_chars_per_report]
            if len(sql) > max_chars_per_report:
                snippet += "\n-- ... (truncated)"
            lines.append(f"\n-- REPORT {i}: {label}")
            lines.append(f"-- File: {fname}")
            lines.append(snippet)

        lines.append("=" * 60)
        return "\n".join(lines)

    def execute_view_query(self, view_name: str, sql: str) -> List[Dict[str, Any]]:
        """Execute a direct SQL query against a view using the data adapter."""
        try:
            from backend.ai_agent.data_adapter import get_adapter
            adapter = get_adapter()
            result = adapter.execute_query(sql)
            logger.info(f"[ViewQueryService] View query returned {len(result or [])} rows")
            return result or []
        except Exception as e:
            logger.error(f"[ViewQueryService] Error executing view query: {e}")
            return []


def get_view_query_service() -> ViewQueryService:
    """Singleton accessor."""
    return ViewQueryService.get_instance()
