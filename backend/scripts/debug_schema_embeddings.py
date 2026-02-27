"""
Debug script to inspect schema embeddings
"""
import sys
import os
from sqlalchemy import text
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.ai_agent.database_service import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    engine = get_engine()
    if not engine:
        logger.error("No DB engine")
        return
        
    with engine.connect() as conn:
        # Check count
        result = conn.execute(text("SELECT count(*) FROM embeddings WHERE table_name = '__schema_metadata__'"))
        count = result.scalar()
        logger.info(f"Total schema embeddings: {count}")
        
        # List all indexed tables
        # res = conn.execute(text("SELECT row_id FROM embeddings WHERE table_name = '__schema_metadata__'"))
        # indexed_tables = [r.row_id for r in res]
        # logger.info(f"Indexed tables: {indexed_tables}")

        # Check adapter schema visibility
        from backend.ai_agent.data_adapter import get_adapter
        adapter = get_adapter()
        schema = adapter.get_schema()
        logger.info(f"Adapter visible tables count: {len(schema)}")
        for t in ["names", "Sales", "sales", "Inventory", "inventory", "Project_59", "project_59"]:
            if t in schema:
                logger.info(f"✅ Table '{t}' EXISTS in schema")
            else:
                logger.info(f"❌ Table '{t}' NOT in schema")
        
        # Check specific tables in embeddings
        targets = ["Sales", "Inventory", "project_59", "sales", "inventory"]
        for t in targets:
            # We store the actual table name in metadata->>'table' or matching row_id
            # row_id for schema is the table name
            res = conn.execute(text(f"SELECT row_id, content_text FROM embeddings WHERE table_name = '__schema_metadata__' AND row_id = '{t}'"))
            row = res.fetchone()
            if row:
                logger.info(f"✅ Found embedding for '{t}': {row.content_text[:100]}...")
            else:
                logger.warning(f"❌ No embedding for '{t}'")
                
        # Check top 5 similarity for 'sales' manually
        logger.info("Checking similarity for 'sales'...")
        # Get vector service just for generating embedding
        from backend.ai_agent.vector_service import get_vector_service
        vs = get_vector_service()
        emb = vs._generate_embedding("sales revenue")
        
        if emb:
            sql = """
                SELECT row_id, 1 - (embedding <=> CAST(:vec AS vector)) as sim 
                FROM embeddings 
                WHERE table_name = '__schema_metadata__'
                ORDER BY sim DESC 
                LIMIT 5
            """
            res = conn.execute(text(sql), {"vec": str(emb)})
            logger.info("Top 5 for 'sales revenue':")
            for r in res:
                logger.info(f"  {r.row_id}: {r.sim}")

if __name__ == "__main__":
    main()
