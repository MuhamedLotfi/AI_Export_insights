"""Quick test: check pgvector availability and backend schema loading"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Engine + schema
from backend.ai_agent.database_service import get_engine
from sqlalchemy import text, inspect

engine = get_engine()
print(f"[OK] Engine: {engine}")

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"[OK] Tables found: {len(tables)}")

# Test 2: pgvector extension availability
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM pg_available_extensions WHERE name = 'vector'"))
    rows = result.fetchall()
    if rows:
        print(f"[OK] pgvector available: {rows[0]}")
    else:
        print("[WARN] pgvector NOT available - you need to install it")
        print("  Run: CREATE EXTENSION vector; in psql, or install pgvector for your PostgreSQL version")

# Test 3: DatabaseAdapter schema
from backend.ai_agent.data_adapter import get_adapter
adapter = get_adapter()
schema = adapter.get_schema()
print(f"[OK] DatabaseAdapter schema: {len(schema)} tables")
print(f"  First 5: {list(schema.keys())[:5]}")

# Test 4: nomic-embed-text
try:
    import ollama
    resp = ollama.embeddings(model="nomic-embed-text", prompt="test")
    emb = resp.get("embedding", [])
    print(f"[OK] Embedding model works, dimensions: {len(emb)}")
except Exception as e:
    print(f"[WARN] Embedding error: {e}")

print("\n--- All tests complete ---")
