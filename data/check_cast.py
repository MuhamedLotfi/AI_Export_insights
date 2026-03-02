import psycopg2
import sys
conn = psycopg2.connect(dbname='ERP_AI', user='postgres', password='postgres_erp', host='localhost', port='5432')
cur = conn.cursor()
try:
    cur.execute("SELECT castsource::regtype, casttarget::regtype, castcontext FROM pg_cast WHERE castsource = 'integer'::regtype AND casttarget = 'boolean'::regtype")
    print(cur.fetchall())
except Exception as e:
    print(e)

try:
    # Try an insert
    cur.execute("CREATE TEMP TABLE t1 (b boolean);")
    cur.execute("INSERT INTO t1 (b) VALUES (0);")
    print("Insert succeeded!")
except Exception as e:
    print("Insert failed:", e)
