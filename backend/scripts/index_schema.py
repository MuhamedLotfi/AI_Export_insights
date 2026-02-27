"""
Script to index database schema for vector search.
Run this to enable dynamic table discovery by the AI agent.
"""
import sys
import os
import logging

# Add project root to path (D:\AI\AI_Export_insights)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai_agent.data_adapter import get_adapter
from backend.ai_agent.vector_service import get_vector_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom descriptions/mappings for key tables to help semantic search
TABLE_DESCRIPTIONS = {
    "users": "User accounts, authentication, roles, and system access. Keywords: user, employee, مستخدم, موظف",
    "user_agents": "Mapping of which users have access to which AI agents",
    "conversations": "History of AI chat sessions and messages",
    "feedback": "User feedback and ratings for AI responses",
    "agents": "Configuration of AI agents and their capabilities",

    # ERP Tables with Arabic keywords
    "EntityInvoices": "Sales invoices, revenue, billing, customer invoices. Contains TotalAmount. Keywords: sales, invoice, revenue, فواتير, مبيعات, فاتورة",
    "Operations": "Projects, jobs, contracts, operational units. Main project table. Keywords: project, operation, job, contract, مشاريع, مشروع, عمليات",
    "PaymentOrders": "Purchase orders, expenses, payments to suppliers, dues, entitlements, disbursements. Keywords: purchase, expense, payment, order, dues, entitlements, disbursement, مشتريات, دفع, توريد, مستحقات, صرف, مدفوعات, صرف مستحقات",
    "PaymentOrderClaims": "Claims, payment requests, contractor claims, officer dues, entitlements. Keywords: claim, request, dues, entitlements, مطالبه, مطالبات, مستخلص, مستحقات, صرف مستحقات",
    "AssignmentOrders": "Sales orders, assignments, job orders. Keywords: assignment, order, sales order, امر بيع, تكليف",
    "Contracts": "Legal contracts, agreements. Keywords: contract, agreement, عقد, عقود",
    "CompanyContracts": "Company specific contracts. Keywords: company contract, contracts",
    "PriceOffers": "Price quotations and offers to clients",
    "Requests": "Service requests and operational workflows",
    "LookupItems": "System lookups, status codes, types. Keywords: lookup, status, type, تعريفات, حالات"
}

def main():
    logger.info("Starting schema indexing...")
    
    # 1. Get Database Adapter
    adapter = get_adapter()
    
    # 2. Get Schema
    logger.info("Fetching database schema...")
    schema = adapter.get_schema()
    logger.info(f"Found {len(schema)} tables")
    
    # 3. Get Vector Service
    vector_service = get_vector_service()
    if not vector_service._ready:
        logger.error("Vector service is not ready/enabled!")
        return

    # 4. Index Schema
    logger.info("Indexing schema into vector store...")
    vector_service.index_schema(schema, TABLE_DESCRIPTIONS)
    
    logger.info("✅ Schema indexing complete!")
    
    # 5. Test Verification
    test_query = "show me sales revenue"
    logger.info(f"Testing discovery with query: '{test_query}'")
    tables = vector_service.find_tables(test_query)
    logger.info(f"Found tables: {tables}")

if __name__ == "__main__":
    main()
