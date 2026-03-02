import psycopg2
conn = psycopg2.connect(dbname='ERP_AI', user='postgres', password='postgres_erp', host='localhost', port='5432')
conn.autocommit = True
cur = conn.cursor()
try:
    cur.execute("UPDATE pg_cast SET castcontext = 'i' WHERE castsource = 'integer'::regtype AND casttarget = 'boolean'::regtype;")
    cur.execute("UPDATE pg_cast SET castcontext = 'i' WHERE castsource = 'smallint'::regtype AND casttarget = 'boolean'::regtype;")
    print("pg_cast updated successfully.")
except Exception as e:
    print("update failed:", e)

# test
try:
    cur.execute("CREATE TEMP TABLE t2 (b boolean);")
    cur.execute("INSERT INTO t2 (b) VALUES (0);")
    cur.execute("INSERT INTO t2 (b) VALUES (1);")
    print("Insert succeeded!")
except Exception as e:
    print("Insert failed:", e)
