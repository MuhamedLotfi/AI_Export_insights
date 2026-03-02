"""Check what view names actually exist in the database."""
import psycopg2

conn = psycopg2.connect(
    host="localhost", database="ERP_AI",
    user="postgres", password="postgres_erp", port=5432
)
cur = conn.cursor()

# Check all non-system views
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.views 
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_name
""")
rows = cur.fetchall()
print(f"Found {len(rows)} user views:")
for schema, name in rows:
    print(f"  schema={schema}  name={name}")

# Try both casings
print("\n--- Testing case-sensitive queries ---")
for view_name in [
    'vw_Customer_Project_Invoices',
    'vw_customer_project_invoices',
    '"vw_Customer_Project_Invoices"',
]:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {view_name}")
        count = cur.fetchone()[0]
        print(f"  OK: {view_name} -> {count} rows")
    except Exception as e:
        conn.rollback()
        print(f"  FAIL: {view_name} -> {e.pgerror.strip()}")

conn.close()
