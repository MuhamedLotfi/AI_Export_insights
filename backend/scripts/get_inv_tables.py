import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        database="ERP_AI",
        user="postgres",
        password="postgres_erp",
        port=5432
    )
    cur = conn.cursor()
    
    tables = ['PaymentOrderInvoices', 'EntityInvoices', 'CompanyInvoices']
    for t in tables:
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{t}' 
            ORDER BY ordinal_position;
        """)
        cols = cur.fetchall()
        print(f"--- Table: {t} ---")
        for c in cols:
            print(f"  {c[0]} : {c[1]}")
            
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
