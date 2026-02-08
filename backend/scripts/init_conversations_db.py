import psycopg2
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import PG_CONFIG

# Override with user specified target DB
TARGET_DB = "ai_insights"
PG_CONFIG["database"] = TARGET_DB

def setup_database():
    print(f"--- Initializing Database: {TARGET_DB} ---")
    print(f"Host: {PG_CONFIG['host']}")
    print(f"User: {PG_CONFIG['user']}")
    
    # 1. Create Database if it doesn't exist
    try:
        # Connect to default 'postgres' db to create new db
        conn = psycopg2.connect(
            host=PG_CONFIG["host"],
            port=PG_CONFIG["port"],
            user=PG_CONFIG["user"],
            password=PG_CONFIG["password"],
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{TARGET_DB}'")
        exists = cur.fetchone()
        
        if not exists:
            print(f"Creating database '{TARGET_DB}'...")
            cur.execute(f"CREATE DATABASE {TARGET_DB}")
        else:
            print(f"Database '{TARGET_DB}' already exists.")
            
        cur.close()
        conn.close()
        
    except psycopg2.OperationalError as e:
        if "password authentication failed" in str(e):
            print("\n[ERROR] Authentication Failed!")
            print(f"The password for user '{PG_CONFIG['user']}' was rejected.")
            print(f"Current configured password: '{PG_CONFIG['password']}'")
            print("Please update 'backend/config.py' or set 'PG_PASSWORD' environment variable.")
            return
        else:
            print(f"Connection error: {e}")
            return
    except Exception as e:
        print(f"Unexpected error creating DB: {e}")
        return

    # 2. Create Tables in the new Database
    try:
        conn = psycopg2.connect(
            host=PG_CONFIG["host"],
            port=PG_CONFIG["port"],
            user=PG_CONFIG["user"],
            password=PG_CONFIG["password"],
            database=TARGET_DB
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Extensions
        print("Enabling extensions (vector, pg_trgm)...")
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        
        # Table
        print("Creating table 'conversations'...")
        sql_script = """
        CREATE TABLE IF NOT EXISTS public.conversations
        (
            id character varying(255) PRIMARY KEY,
            user_id integer,
            conversation_id character varying(255),
            query text NOT NULL,
            response text NOT NULL,
            agents_used text[],
            embedding vector(1024),
            metadata jsonb,
            "timestamp" timestamp without time zone DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS conversations_embedding_idx 
            ON public.conversations USING hnsw (embedding vector_cosine_ops);
            
        CREATE INDEX IF NOT EXISTS idx_conversations_query_trgm 
            ON public.conversations USING gin (query gin_trgm_ops);
        """
        cur.execute(sql_script)
        
        print("✅ Database setup completed successfully!")
        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    setup_database()
