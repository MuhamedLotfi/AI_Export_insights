"""
Script to index project data for vector search.
Indexes key text fields from:
- Operations (Projects)
- EntityInvoices (Sales/Invoices)
- Contracts
"""
import os
import sys
import logging

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.ai_agent.vector_service import get_vector_service
from backend.ai_agent.data_adapter import get_adapter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def index_data():
    logger.info("Starting project data indexing...")
    
    vector = get_vector_service()
    if not vector._ready:
        logger.error("Vector service not ready. Check configuration.")
        return

    adapter = get_adapter()
    
    # 1. Index Operations (Projects)
    # Important fields: OperationName, Beneficiary, OperationType
    operations = adapter.get_all("Operations")
    if operations:
        logger.info(f"Indexing {len(operations)} Operations...")
        vector.index_table(
            table_name="Operations",
            rows=operations,
            text_columns=["OperationName", "Beneficiary", "OperationType", "StatusLookupItemId"]
        )
    
    # 2. Index EntityInvoices (Sales)
    # Important fields: Subject, Notes
    invoices = adapter.get_all("EntityInvoices")
    if invoices:
        logger.info(f"Indexing {len(invoices)} Invoices...")
        # Only index invoices with meaningful text (Subject or Notes)
        # We limit to last 500 to avoid overwhelming if strict
        recent_invoices = invoices[-500:] 
        vector.index_table(
            table_name="EntityInvoices",
            rows=recent_invoices,
            text_columns=["Subject", "Notes", "Wording"]
        )

    # 3. Index Contracts
    # Important fields: Subject, ContractName
    contracts = adapter.get_all("Contracts")
    if contracts:
        logger.info(f"Indexing {len(contracts)} Contracts...")
        vector.index_table(
            table_name="Contracts",
            rows=contracts,
            text_columns=["Subject", "ContractName", "BeneficiaryName"]
        )

    logger.info("Indexing complete.")

if __name__ == "__main__":
    index_data()
