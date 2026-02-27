"""
Script to index ALL tables from the ERP_AI database for vector search.
Uses batch embedding for performance (BAAI/bge-m3 via SentenceTransformer).

Usage:
  python -m backend.scripts.index_all_tables              # Index all tables
  python -m backend.scripts.index_all_tables --table Operations  # Index one table
  python -m backend.scripts.index_all_tables --skip-existing     # Skip already-indexed tables
  python -m backend.scripts.index_all_tables --reset             # Clear all embeddings first
"""
import sys
import os
import argparse
import logging
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai_agent.data_adapter import get_adapter
from backend.ai_agent.vector_service import get_vector_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tables to skip (system/internal tables)
SKIP_TABLES = {
    "embeddings",
    "__EFMigrationsHistory",
    "conversations",
    "conversation_feedback",
    "sysdiagrams",
}

# Custom descriptions/mappings for key tables (Arabic + English keywords)
TABLE_DESCRIPTIONS = {
    "users": "User accounts, authentication, roles. Keywords: user, employee, مستخدم, موظف",
    "user_agents": "Mapping of which users have access to which AI agents",
    "agents": "Configuration of AI agents and their capabilities",

    # ERP core tables
    "EntityInvoices": "Sales invoices, revenue, billing, customer invoices. Contains TotalAmount. Keywords: sales, invoice, revenue, فواتير, مبيعات, فاتورة, ايراد",
    "Operations": "Projects, jobs, contracts, operational units. Main project table. Keywords: project, operation, job, contract, مشاريع, مشروع, عمليات",
    "PaymentOrders": "Purchase orders, expenses, payments to suppliers. Keywords: purchase, expense, payment, order, مشتريات, دفع, توريد, أمر شراء",
    "PaymentOrderClaims": "Claims, payment requests, contractor claims. Keywords: claim, request, مطالبه, مطالبات, مستخلص",
    "AssignmentOrders": "Sales orders, assignments, job orders. Keywords: assignment, order, sales order, امر بيع, تكليف",
    "Contracts": "Legal contracts, agreements. Keywords: contract, agreement, عقد, عقود",
    "CompanyContracts": "Company specific contracts. Keywords: company contract, contracts",
    "PriceOffers": "Price quotations and offers to clients. Keywords: quotation, offer, عرض سعر, عروض",
    "Requests": "Service requests and operational workflows. Keywords: request, طلب",
    "LookupItems": "System lookups, status codes, types. Keywords: lookup, status, type, تعريفات, حالات",
    "Lookups": "Lookup categories and groups. Keywords: lookup, category",
    "TaxExemptions": "Tax exemption records. Keywords: tax, exemption, ضريبة, اعفاء",
    "TaxExemptionInvoices": "Tax exemption invoices. Keywords: tax, invoice, ضريبة, فاتورة",
    "PaymentOrderInvoices": "Purchase invoices linked to payment orders. Keywords: purchase invoice, فاتورة مشتريات",
    "IndicativeQuotations": "Indicative price quotations. Keywords: quotation, indicative, عرض أسعار",
    "Users": "System users and their details. Keywords: user, مستخدم",
    "Roles": "User roles and permissions. Keywords: role, permission, دور, صلاحية",
    "BankAccounts": "Bank account details. Keywords: bank, account, بنك, حساب",
    "Branches": "Company branches and locations. Keywords: branch, location, فرع",
    "Entities": "Business entities (customers, suppliers). Keywords: entity, customer, supplier, عميل, مورد, جهة",
}

# Columns to prefer for text content (per table)
# If not listed, auto-detection will be used
PREFERRED_TEXT_COLUMNS = {
    "Operations": ["OperationName", "Beneficiary", "OperationType", "StatusLookupItemId", "OperationDate"],
    "EntityInvoices": ["Subject", "Notes", "Wording", "TotalAmount", "InvoiceDate"],
    "Contracts": ["Subject", "ContractName", "BeneficiaryName", "ContractDate"],
    "CompanyContracts": ["Subject", "ContractName", "BeneficiaryName"],
    "PaymentOrders": ["Subject", "Notes", "TotalAmount"],
    "PaymentOrderClaims": ["Subject", "Notes", "TotalAmount"],
    "AssignmentOrders": ["Subject", "Notes", "TotalAmount"],
    "PriceOffers": ["Subject", "Notes", "TotalAmount"],
    "Requests": ["Subject", "Notes", "RequestDate"],
    "Users": ["FullName", "Email", "UserName"],
    "Entities": ["EntityName", "EntityType", "Phone", "Email"],
    "Branches": ["BranchName", "Address", "Phone"],
}


def index_all_tables(
    target_table: str = None,
    skip_existing: bool = False,
    reset: bool = False,
    max_rows_per_table: int = 2000,
    batch_size: int = 64
):
    """Index all (or specific) tables from ERP_AI database."""

    start_time = time.time()
    logger.info("=" * 60)
    logger.info("  ERP_AI Full Database Vector Indexing")
    logger.info("=" * 60)

    # 1. Get services
    adapter = get_adapter()
    vector = get_vector_service()

    if not vector._ready:
        logger.error("Vector service is not ready! Check configuration.")
        return

    logger.info(f"Model: {vector.embedding_model} ({vector.dimensions} dims)")
    logger.info(f"Provider: {vector.provider}")

    # 2. Get schema
    schema = adapter.get_schema()
    logger.info(f"Database tables found: {len(schema)}")

    # Filter to target table if specified
    if target_table:
        if target_table not in schema:
            logger.error(f"Table '{target_table}' not found in database!")
            logger.info(f"Available tables: {sorted(schema.keys())}")
            return
        schema = {target_table: schema[target_table]}
        logger.info(f"Targeting single table: {target_table}")

    # 3. Reset if requested
    if reset:
        logger.warning("Resetting all data embeddings...")
        for table_name in schema:
            if table_name in SKIP_TABLES:
                continue
            deleted = vector.clear_table(table_name)
            if deleted > 0:
                logger.info(f"  Cleared {deleted} embeddings from {table_name}")
        logger.info("Reset complete.")

    # 4. Index schema metadata first
    logger.info("\n--- Indexing Schema Metadata ---")
    vector.index_schema(schema, TABLE_DESCRIPTIONS)

    # 5. Index data from each table
    logger.info("\n--- Indexing Table Data ---")
    total_indexed = 0
    table_results = {}

    tables_to_process = sorted(schema.keys())

    for i, table_name in enumerate(tables_to_process, 1):
        if table_name in SKIP_TABLES:
            logger.info(f"[{i}/{len(tables_to_process)}] Skipping system table: {table_name}")
            continue

        logger.info(f"\n[{i}/{len(tables_to_process)}] Processing: {table_name}")

        try:
            # Get rows (with safety limit)
            rows = adapter.get_all(table_name)
            if not rows:
                logger.info(f"  [{table_name}] No rows found, skipping.")
                table_results[table_name] = {"rows": 0, "indexed": 0}
                continue

            # Cap rows
            if len(rows) > max_rows_per_table:
                logger.info(f"  [{table_name}] Capping from {len(rows)} to {max_rows_per_table} rows")
                rows = rows[:max_rows_per_table]

            logger.info(f"  [{table_name}] {len(rows)} rows to process")

            # Get preferred columns or None for auto-detect
            text_cols = PREFERRED_TEXT_COLUMNS.get(table_name, None)

            # Use batch indexing
            indexed = vector.index_rows_batch(
                table_name=table_name,
                rows=rows,
                text_columns=text_cols,
                batch_size=batch_size,
                skip_existing=skip_existing
            )

            total_indexed += indexed
            table_results[table_name] = {"rows": len(rows), "indexed": indexed}

        except Exception as e:
            logger.error(f"  [{table_name}] Error: {e}")
            table_results[table_name] = {"rows": 0, "indexed": 0, "error": str(e)}

    # 6. Summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 60)
    logger.info("  INDEXING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total time: {elapsed:.1f}s")
    logger.info(f"Total rows indexed: {total_indexed}")
    logger.info(f"\nPer-table breakdown:")

    for table_name, result in sorted(table_results.items()):
        status = "OK" if result.get("indexed", 0) > 0 else ("SKIP" if result.get("rows", 0) == 0 else "EMPTY")
        if result.get("error"):
            status = "ERROR"
        logger.info(f"  {table_name:40s} | rows={result['rows']:5d} | indexed={result.get('indexed', 0):5d} | {status}")

    # Final stats
    stats = vector.get_stats()
    logger.info(f"\nVector DB total embeddings: {stats.get('total_embeddings', 'N/A')}")
    logger.info(f"Tables in vector DB: {stats.get('tables', {})}")
    logger.info("\nDone!")


def main():
    parser = argparse.ArgumentParser(description="Index ERP_AI tables for vector search")
    parser.add_argument("--table", type=str, help="Index only this specific table")
    parser.add_argument("--skip-existing", action="store_true", help="Skip tables that already have embeddings")
    parser.add_argument("--reset", action="store_true", help="Clear all data embeddings before indexing")
    parser.add_argument("--max-rows", type=int, default=2000, help="Max rows per table (default: 2000)")
    parser.add_argument("--batch-size", type=int, default=64, help="Embedding batch size (default: 64)")

    args = parser.parse_args()

    index_all_tables(
        target_table=args.table,
        skip_existing=args.skip_existing,
        reset=args.reset,
        max_rows_per_table=args.max_rows,
        batch_size=args.batch_size
    )


if __name__ == "__main__":
    main()
