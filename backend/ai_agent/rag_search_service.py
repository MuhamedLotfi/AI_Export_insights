"""
RAG Search Service - Enhanced hybrid search engine.
Combines vector similarity search with keyword matching and table relevance scoring
for significantly better search results than pure vector search.

This service runs alongside the existing search system for testing, and can be
swapped in as the primary search engine when ready.
"""
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result with scoring details"""
    content: str
    table_name: str
    row_id: str
    vector_score: float = 0.0
    keyword_score: float = 0.0
    table_relevance_score: float = 0.0
    final_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "table_name": self.table_name,
            "row_id": self.row_id,
            "vector_score": round(self.vector_score, 4),
            "keyword_score": round(self.keyword_score, 4),
            "table_relevance_score": round(self.table_relevance_score, 4),
            "final_score": round(self.final_score, 4),
            "metadata": self.metadata,
        }


# Table relevance keywords (query term → tables that are relevant)
TABLE_RELEVANCE_MAP = {
    # English keywords
    "invoice": ["EntityInvoices", "PaymentOrderInvoices", "TaxExemptionInvoices"],
    "invoices": ["EntityInvoices", "PaymentOrderInvoices", "TaxExemptionInvoices"],
    "sales": ["EntityInvoices", "AssignmentOrders"],
    "revenue": ["EntityInvoices"],
    "purchase": ["PaymentOrders", "PaymentOrderInvoices"],
    "order": ["AssignmentOrders", "PaymentOrders"],
    "project": ["Operations"],
    "operation": ["Operations"],
    "contract": ["Contracts", "CompanyContracts"],
    "claim": ["PaymentOrderClaims"],
    "quotation": ["PriceOffers", "IndicativeQuotations"],
    "offer": ["PriceOffers"],
    "tax": ["TaxExemptions", "TaxExemptionInvoices"],
    "user": ["Users"],
    "branch": ["Branches"],
    "entity": ["Entities"],
    "customer": ["Entities"],
    "supplier": ["Entities"],
    "bank": ["BankAccounts"],
    "lookup": ["Lookups", "LookupItems"],
    "request": ["Requests"],

    # Arabic keywords
    "فاتورة": ["EntityInvoices", "PaymentOrderInvoices"],
    "فواتير": ["EntityInvoices", "PaymentOrderInvoices"],
    "مبيعات": ["EntityInvoices", "AssignmentOrders"],
    "مشتريات": ["PaymentOrders", "PaymentOrderInvoices"],
    "مشروع": ["Operations"],
    "مشاريع": ["Operations"],
    "عمليات": ["Operations"],
    "عقد": ["Contracts", "CompanyContracts"],
    "عقود": ["Contracts", "CompanyContracts"],
    "مطالبة": ["PaymentOrderClaims"],
    "مطالبات": ["PaymentOrderClaims"],
    "عرض": ["PriceOffers", "IndicativeQuotations"],
    "ضريبة": ["TaxExemptions"],
    "أمر بيع": ["AssignmentOrders"],
    "أمر شراء": ["PaymentOrders"],
    "عميل": ["Entities"],
    "مورد": ["Entities"],
    "فرع": ["Branches"],
    "بنك": ["BankAccounts"],
    "مستحقات": ["PaymentOrders", "PaymentOrderClaims", "PaymentOrderDeductions"],
    "صرف": ["PaymentOrders", "PaymentOrderClaims"],
    "صرف مستحقات": ["PaymentOrders", "PaymentOrderClaims", "PaymentOrderDeductions"],
    "دفع": ["PaymentOrders", "PaymentOrderClaims"],
    "مدفوعات": ["PaymentOrders", "PaymentOrderClaims"],
    "مستخلص": ["PaymentOrderClaims", "PaymentOrderClaimItems"],
    "dues": ["PaymentOrders", "PaymentOrderClaims", "PaymentOrderDeductions"],
    "entitlements": ["PaymentOrders", "PaymentOrderClaims"],
    "payment": ["PaymentOrders", "PaymentOrderClaims"],
    "disbursement": ["PaymentOrders", "PaymentOrderClaims"],
}


class RAGSearchService:
    """
    Enhanced RAG search with hybrid vector + keyword + table relevance scoring.

    Scoring formula:
        final_score = w_vector * vector_sim + w_keyword * keyword_match + w_table * table_relevance

    Default weights: vector=0.70, keyword=0.20, table=0.10
    """

    _instance: Optional['RAGSearchService'] = None

    @classmethod
    def get_instance(cls) -> 'RAGSearchService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(
        self,
        weight_vector: float = 0.70,
        weight_keyword: float = 0.20,
        weight_table: float = 0.10,
    ):
        self.w_vector = weight_vector
        self.w_keyword = weight_keyword
        self.w_table = weight_table

    def search(
        self,
        query: str,
        top_k: int = 10,
        table_filter: Optional[str] = None,
        vector_candidates: int = 50,
    ) -> List[SearchResult]:
        """
        Perform hybrid search combining vector similarity, keyword matching,
        and table relevance scoring.

        Args:
            query: The search query (English or Arabic)
            top_k: Number of results to return
            table_filter: Optional table name to restrict search to
            vector_candidates: Number of vector results to fetch before re-ranking

        Returns:
            List of SearchResult objects, sorted by final_score descending
        """
        from backend.ai_agent.vector_service import get_vector_service
        vector_svc = get_vector_service()

        if not vector_svc._ready:
            logger.warning("Vector service not ready for RAG search")
            return []

        # Step 1: Get vector candidates (fetch more than needed for re-ranking)
        raw_results = vector_svc.semantic_search(
            query,
            top_k=vector_candidates,
            table_filter=table_filter
        )

        if not raw_results:
            return []

        # Step 2: Compute keyword and table relevance scores, then re-rank
        query_terms = self._extract_terms(query)
        relevant_tables = self._get_relevant_tables(query)

        results = []
        for raw in raw_results:
            content = raw.get("content_text", "")
            table_name = raw.get("table_name", "")
            row_id = raw.get("row_id", "")
            vector_sim = float(raw.get("similarity", 0))
            metadata = raw.get("metadata", {})

            # Skip schema metadata entries from results (unless explicitly filtering)
            if table_name == "__schema_metadata__" and not table_filter:
                continue

            # Keyword score
            keyword_score = self._compute_keyword_score(content, query_terms)

            # Table relevance score
            table_score = 1.0 if table_name in relevant_tables else 0.0

            # Final hybrid score
            final_score = (
                self.w_vector * vector_sim +
                self.w_keyword * keyword_score +
                self.w_table * table_score
            )

            results.append(SearchResult(
                content=content,
                table_name=table_name,
                row_id=row_id,
                vector_score=vector_sim,
                keyword_score=keyword_score,
                table_relevance_score=table_score,
                final_score=final_score,
                metadata=metadata if isinstance(metadata, dict) else {},
            ))

        # Sort by final score descending
        results.sort(key=lambda r: r.final_score, reverse=True)

        return results[:top_k]

    def search_with_context(
        self,
        query: str,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """
        Enhanced search for the AI agent pipeline.
        Returns both relevant rows AND their source table schemas + SQL hints.
        """
        results = self.search(query, top_k=top_k)

        # Collect unique tables from results
        result_tables = list(set(r.table_name for r in results if r.table_name))

        # Get schema info for discovered tables
        table_schemas = {}
        try:
            from backend.ai_agent.data_adapter import get_adapter
            adapter = get_adapter()
            full_schema = adapter.get_schema()
            for table in result_tables:
                if table in full_schema:
                    table_schemas[table] = full_schema[table]
        except Exception as e:
            logger.warning(f"Could not fetch schema info: {e}")

        # Build SQL hints
        sql_hints = []
        for table in result_tables:
            if "invoice" in table.lower():
                sql_hints.append(f'Use "TotalAmount" for revenue from "{table}"')
            if table == "Operations":
                sql_hints.append('Use "OperationName" for project names')

        return {
            "results": [r.to_dict() for r in results],
            "result_count": len(results),
            "discovered_tables": result_tables,
            "table_schemas": table_schemas,
            "sql_hints": sql_hints,
            "query": query,
        }

    # ── Scoring Helpers ───────────────────────────────────────────────

    def _extract_terms(self, query: str) -> List[str]:
        """Extract meaningful terms from query for keyword matching."""
        # Keep Arabic characters, split on spaces/punctuation
        terms = re.findall(r'[\w\u0600-\u06FF]+', query.lower())
        # Filter out very short terms (less than 2 chars)
        stopwords = {"the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "and", "or", "me", "my", "show", "get", "from"}
        return [t for t in terms if len(t) > 1 and t not in stopwords]

    def _compute_keyword_score(self, content: str, query_terms: List[str]) -> float:
        """Compute keyword match score (0.0 to 1.0)."""
        if not query_terms or not content:
            return 0.0

        content_lower = content.lower()
        matches = sum(1 for term in query_terms if term in content_lower)
        return min(matches / len(query_terms), 1.0)

    def _get_relevant_tables(self, query: str) -> set:
        """Get set of tables relevant to the query based on keyword mapping."""
        relevant = set()
        query_lower = query.lower()

        for keyword, tables in TABLE_RELEVANCE_MAP.items():
            if keyword in query_lower or keyword in query:
                relevant.update(tables)

        return relevant


def get_rag_search_service() -> RAGSearchService:
    """Get the singleton RAGSearchService"""
    return RAGSearchService.get_instance()
