import psycopg2
conn = psycopg2.connect(dbname='ERP_AI', user='postgres', password='postgres_erp', host='localhost', port='5432')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='CompanyInvoices'")
print([r[0] for r in cur.fetchall()])
