import psycopg2

conn = psycopg2.connect(dbname='ERP_AI', user='postgres', password='postgres_erp', host='localhost', port='5432')
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute('ALTER TABLE "Entities" ADD COLUMN IF NOT EXISTS "DefaultCheckFee" TEXT')
    print("Added DefaultCheckFee to Entities")
except Exception as e:
    print(e)
    
try:
    cur.execute('ALTER TABLE "CompanyInvoices" ADD COLUMN IF NOT EXISTS "ElectronicInvoiceAttachmentFileId" INTEGER')
    print("Added ElectronicInvoiceAttachmentFileId to CompanyInvoices")
except Exception as e:
    print(e)

try:
    cur.execute('ALTER TABLE "EntityInvoices" ADD COLUMN IF NOT EXISTS "TaxExemptionId" INTEGER')
    print("Added TaxExemptionId to EntityInvoices")
except Exception as e:
    print(e)
