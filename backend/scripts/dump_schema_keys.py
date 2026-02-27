"""
Dump schema keys to file
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
        keys = sorted(list(schema.keys()))
        
        with open("schema_dump.txt", "w", encoding="utf-8") as f:
            for k in keys:
                f.write(f"{k}\n")
                
        logger.info(f"Dumped {len(keys)} tables to schema_dump.txt")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    main()
