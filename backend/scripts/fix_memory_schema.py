import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
logging.basicConfig(level=logging.INFO, format='%(message)s')

from backend.ai_agent.database_service import get_engine
from sqlalchemy import text

def add_embedding_column():
    engine = get_engine()
    if not engine:
        print("Could not connect to database")
        sys.exit(1)
        
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS embedding vector(1024);"))
            # Also create an index for faster similarity search
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS conversations_embedding_idx ON conversations "
                "USING hnsw (embedding vector_cosine_ops);"
            ))
            print("Successfully added 'embedding' column to 'conversations' table and created HNSW index.")
        except Exception as e:
            print(f"Error adding column: {e}")
            sys.exit(1)

if __name__ == "__main__":
    add_embedding_column()
