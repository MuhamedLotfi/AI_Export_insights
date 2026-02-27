"""
Check columns of potential candidate tables
"""
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai_agent.data_adapter import get_adapter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        adapter = get_adapter()
        schema = adapter.get_schema()
        
        candidates = ["Contracts", "LookupItems", "CompanyContracts"]
        
        with open("columns_dump.txt", "w", encoding="utf-8") as f:
            for table in candidates:
                if table in schema:
                    cols = schema[table]
                    f.write(f"\n--- {table} Columns ---\n")
                    f.write(f"{cols}\n")
                    
                    # Check for key columns used in ProcessingAgent
                    if "total_sales_amount" in cols:
                        f.write(f"✅ Found 'total_sales_amount' in {table}\n")
                    if "project_name" in cols:
                         f.write(f"✅ Found 'project_name' in {table}\n")
        
        logger.info("Dumped columns to columns_dump.txt")

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
