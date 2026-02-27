"""
Automated test script for RAG search quality.
Compares old (pure vector) vs new (hybrid RAG) search results.

Usage:
  python -m backend.scripts.test_rag_search
"""
import sys
import os
import logging
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── Test Queries ──────────────────────────────────────────────────────
# Each query has expected tables that should appear in the top results.
TEST_QUERIES = [
    {
        "query": "show me sales invoices",
        "expected_tables": ["EntityInvoices"],
        "description": "English: sales invoices lookup"
    },
    {
        "query": "project contracts and agreements",
        "expected_tables": ["Contracts", "Operations"],
        "description": "English: project contracts"
    },
    {
        "query": "فواتير المبيعات",
        "expected_tables": ["EntityInvoices"],
        "description": "Arabic: sales invoices"
    },
    {
        "query": "مشاريع وعمليات",
        "expected_tables": ["Operations"],
        "description": "Arabic: projects and operations"
    },
    {
        "query": "purchase orders from suppliers",
        "expected_tables": ["PaymentOrders"],
        "description": "English: purchase orders"
    },
    {
        "query": "أوامر الشراء",
        "expected_tables": ["PaymentOrders"],
        "description": "Arabic: purchase orders"
    },
    {
        "query": "total revenue by project",
        "expected_tables": ["EntityInvoices", "Operations"],
        "description": "English: revenue analysis"
    },
    {
        "query": "مطالبات المقاولين",
        "expected_tables": ["PaymentOrderClaims"],
        "description": "Arabic: contractor claims"
    },
    {
        "query": "price quotation offers",
        "expected_tables": ["PriceOffers", "IndicativeQuotations"],
        "description": "English: quotations"
    },
    {
        "query": "عروض الأسعار",
        "expected_tables": ["PriceOffers", "IndicativeQuotations"],
        "description": "Arabic: price offers"
    },
    {
        "query": "tax exemption invoices",
        "expected_tables": ["TaxExemptions", "TaxExemptionInvoices"],
        "description": "English: tax exemptions"
    },
    {
        "query": "عقود الشركة",
        "expected_tables": ["Contracts", "CompanyContracts"],
        "description": "Arabic: company contracts"
    },
]


def run_tests():
    """Run comparison tests between old and new search."""

    # Import services
    from backend.ai_agent.vector_service import get_vector_service
    from backend.ai_agent.rag_search_service import get_rag_search_service

    vector_svc = get_vector_service()
    rag_svc = get_rag_search_service()

    if not vector_svc._ready:
        logger.error("Vector service not ready! Make sure to run index_all_tables.py first.")
        return

    # Get stats
    stats = vector_svc.get_stats()
    logger.info(f"\nVector DB Stats:")
    logger.info(f"  Total embeddings: {stats.get('total_embeddings', 0)}")
    logger.info(f"  Tables indexed: {len(stats.get('tables', {}))}")

    if stats.get('total_embeddings', 0) == 0:
        logger.error("No embeddings found! Run: python -m backend.scripts.index_all_tables")
        return

    # Run tests
    logger.info("\n" + "=" * 80)
    logger.info("  RAG SEARCH QUALITY TEST")
    logger.info("=" * 80)

    old_pass = 0
    new_pass = 0
    total = len(TEST_QUERIES)

    for i, test in enumerate(TEST_QUERIES, 1):
        query = test["query"]
        expected = set(test["expected_tables"])
        desc = test["description"]

        logger.info(f"\n--- Test {i}/{total}: {desc} ---")
        logger.info(f"  Query: \"{query}\"")
        logger.info(f"  Expected tables: {expected}")

        # OLD: Pure vector search
        start = time.time()
        old_results = vector_svc.semantic_search(query, top_k=10)
        old_time = time.time() - start

        old_tables = set()
        old_scores = []
        for r in old_results:
            tn = r.get("table_name", "")
            if tn != "__schema_metadata__":
                old_tables.add(tn)
                old_scores.append(float(r.get("similarity", 0)))

        old_hit = bool(expected & old_tables)
        if old_hit:
            old_pass += 1

        # NEW: Hybrid RAG search
        start = time.time()
        new_results = rag_svc.search(query, top_k=10)
        new_time = time.time() - start

        new_tables = set(r.table_name for r in new_results)
        new_scores = [r.final_score for r in new_results]

        new_hit = bool(expected & new_tables)
        if new_hit:
            new_pass += 1

        # Report
        old_status = "PASS" if old_hit else "FAIL"
        new_status = "PASS" if new_hit else "FAIL"

        logger.info(f"\n  OLD (Vector Only):")
        logger.info(f"    Status: {old_status} | Time: {old_time:.3f}s")
        logger.info(f"    Found tables: {old_tables}")
        if old_scores:
            logger.info(f"    Score range: {min(old_scores):.4f} - {max(old_scores):.4f}")
        for r in old_results[:3]:
            tn = r.get("table_name", "")
            sim = float(r.get("similarity", 0))
            content = r.get("content_text", "")[:80]
            logger.info(f"    [{tn}] sim={sim:.4f} | {content}...")

        logger.info(f"\n  NEW (Hybrid RAG):")
        logger.info(f"    Status: {new_status} | Time: {new_time:.3f}s")
        logger.info(f"    Found tables: {new_tables}")
        if new_scores:
            logger.info(f"    Score range: {min(new_scores):.4f} - {max(new_scores):.4f}")
        for r in new_results[:3]:
            logger.info(f"    [{r.table_name}] final={r.final_score:.4f} (vec={r.vector_score:.4f} kw={r.keyword_score:.4f} tbl={r.table_relevance_score:.1f}) | {r.content[:80]}...")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("  FINAL RESULTS")
    logger.info("=" * 80)
    logger.info(f"  OLD (Pure Vector):  {old_pass}/{total} passed ({old_pass/total*100:.0f}%)")
    logger.info(f"  NEW (Hybrid RAG):   {new_pass}/{total} passed ({new_pass/total*100:.0f}%)")

    improvement = new_pass - old_pass
    if improvement > 0:
        logger.info(f"\n  +{improvement} improvement with hybrid RAG search!")
    elif improvement == 0:
        logger.info(f"\n  Same accuracy. Check individual scores for quality differences.")
    else:
        logger.info(f"\n  {improvement} regression — review scoring weights.")

    logger.info("\nDone!")


if __name__ == "__main__":
    run_tests()
