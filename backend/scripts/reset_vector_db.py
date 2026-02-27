"""
Script to reset the vector database.
run this when changing embedding models/dimensions.
"""
import os
import sys
import logging
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.ai_agent.database_service import get_engine
from backend.config import VECTOR_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_db():
    logger.info("Resetting vector database table...")
    
    engine = get_engine()
    if not engine:
        logger.error("Database engine not available.")
        return

    dim = VECTOR_CONFIG["embedding_dimensions"]
    model = VECTOR_CONFIG["embedding_model"]
    
    logger.info(f"Target Configuration -> Model: {model}, Dimensions: {dim}")

    try:
        with engine.connect() as conn:
            # Drop existing table
            logger.info("Dropping table 'embeddings'...")
            conn.execute(text("DROP TABLE IF EXISTS embeddings"))
            conn.commit()
            
            # Recreate with new dimensions
            logger.info(f"Creating table 'embeddings' with vector({dim})...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.execute(text(f'''
                CREATE TABLE embeddings (
                    id SERIAL PRIMARY KEY,
                    table_name VARCHAR(255) NOT NULL,
                    row_id VARCHAR(255),
                    content_text TEXT NOT NULL,
                    metadata JSONB,
                    embedding vector({dim}),
                    created_at TIMESTAMP DEFAULT NOW()
                )
            '''))
            conn.commit()
            
            # Create Index
            logger.info("Creating IFVFlat index...")
            conn.execute(text("""
                CREATE INDEX idx_embeddings_vector
                ON embeddings USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
            """))
            conn.commit()
            
        logger.info("✅ Database reset complete. You can now run the indexing script.")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")

if __name__ == "__main__":
    reset_db()
