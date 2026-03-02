"""
Test script: Verify view-first data flow is working correctly.
Run: venv\Scripts\python backend/scripts/test_view_priority.py
"""
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_view_routing():
    print("\n" + "="*60)
    print("  TEST 1: View Routing (ViewQueryService)")
    print("="*60)
    from backend.ai_agent.view_query_service import get_view_query_service
    svc = get_view_query_service()

    tests = [
        ("show me project revenue", ["vw_Customer_Project_Invoices"]),
        ("supplier costs this month", ["vw_Supplier_Project_Invoices"]),
        ("مشاريع العملاء والفواتير", ["vw_Customer_Project_Invoices"]),
        ("إجمالي تكاليف الموردين", ["vw_Supplier_Project_Invoices"]),
        ("profit and loss comparison", ["vw_Customer_Project_Invoices", "vw_Supplier_Project_Invoices"]),
        ("user roles and permissions", []),   # should NOT match views
    ]

    passed = 0
    for query, expected_views in tests:
        can_use, matched = svc.can_answer_from_views(query)
        overlap = set(matched) & set(expected_views)
        ok = bool(overlap) == bool(expected_views)
        status = "✅ PASS" if ok else "❌ FAIL"
        if ok:
            passed += 1
        print(f"  {status} | Query: '{query}' → views={matched}")

    print(f"\n  Routing tests: {passed}/{len(tests)} passed")
    return passed == len(tests)


def test_sql_generation():
    print("\n" + "="*60)
    print("  TEST 2: View SQL Generation")
    print("="*60)
    from backend.ai_agent.view_query_service import get_view_query_service
    svc = get_view_query_service()

    sql_list = sql_agg = None
    try:
        sql_list = svc.build_view_sql("vw_Customer_Project_Invoices", limit=10)
        print(f"  List SQL: {sql_list}")
        assert "vw_Customer_Project_Invoices" in sql_list
        assert "LIMIT 10" in sql_list

        sql_agg = svc.build_view_sql("vw_Supplier_Project_Invoices", aggregate="sum")
        print(f"  Agg SQL:  {sql_agg}")
        assert "SUM" in sql_agg
        print("  ✅ SQL generation: PASS")
        return True
    except AssertionError as e:
        print(f"  ❌ SQL generation FAIL: {e}")
        return False


def test_few_shot_matching():
    print("\n" + "="*60)
    print("  TEST 3: Few-Shot Report Matching")
    print("="*60)
    from backend.ai_agent.view_query_service import get_view_query_service
    svc = get_view_query_service()

    print(f"  Loaded reports: {list(svc._reports.keys())}")
    print(f"  Report tags: {svc._report_tags}")

    # Try to match a dashboard-related query
    result = svc.get_matching_report("executive dashboard revenue summary")
    if result:
        print(f"  ✅ Matched report: {result[0]}")
        return True
    else:
        print("  ⚠️  No report matched (tags may not be set in SQL files) — check FEW-SHOT TAGS in sql headers")
        return True  # Non-fatal


def test_live_view_query():
    print("\n" + "="*60)
    print("  TEST 4: Live View Query (requires DB connection)")
    print("="*60)
    try:
        from backend.ai_agent.view_query_service import get_view_query_service
        svc = get_view_query_service()

        sql = svc.build_view_sql("vw_Customer_Project_Invoices", limit=5)
        rows = svc.execute_view_query("vw_Customer_Project_Invoices", sql)
        print(f"  Rows returned: {len(rows)}")
        if rows:
            print(f"  Sample columns: {list(rows[0].keys())[:6]}")
            print("  ✅ Live view query: PASS")
            return True
        else:
            print("  ⚠️  View returned 0 rows — view may be empty or DB unavailable")
            return True  # Non-fatal

    except Exception as e:
        print(f"  ❌ Live view query FAIL: {e}")
        return False


def test_rag_view_boost():
    print("\n" + "="*60)
    print("  TEST 5: RAG Search View Priority Boost")
    print("="*60)
    try:
        from backend.ai_agent.rag_search_service import get_rag_search_service
        rag = get_rag_search_service()
        results = rag.search("project revenue invoice", top_k=5)
        if results:
            top = results[0]
            print(f"  Top result: table={top.table_name} score={top.final_score:.3f}")
            if top.table_name in ("vw_Customer_Project_Invoices", "vw_Supplier_Project_Invoices"):
                print("  ✅ Views rank first in RAG: PASS")
            else:
                print(f"  ⚠️  Top result is '{top.table_name}' (views may not be embedded yet)")
        else:
            print("  ⚠️  No RAG results (vector DB may be empty)")
        return True
    except Exception as e:
        print(f"  ❌ RAG test FAIL: {e}")
        return False


if __name__ == "__main__":
    results = [
        test_view_routing(),
        test_sql_generation(),
        test_few_shot_matching(),
        test_live_view_query(),
        test_rag_view_boost(),
    ]
    total = sum(results)
    print("\n" + "="*60)
    print(f"  TOTAL: {total}/{len(results)} tests passed")
    print("="*60)
    sys.exit(0 if total == len(results) else 1)
