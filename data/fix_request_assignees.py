import psycopg2
import sys

DB_NAME = "ERP_AI"
DB_USER = "postgres"
DB_PASSWORD = "postgres_erp"
DB_HOST = "localhost"
DB_PORT = "5432"

def fix_table():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.autocommit = True
        cursor = conn.cursor()

        print("Dropping problematic indexes on RequestAssignees...")
        cursor.execute('DROP INDEX IF EXISTS "IX_RequestAssignees_RequestId_RoleId"')
        cursor.execute('DROP INDEX IF EXISTS "IX_RequestAssignees_RequestId_RoleId_AssigneeId"')

        print("Converting RequestAssignees.IsDeleted to boolean...")
        # Check if already boolean
        cursor.execute("SELECT data_type FROM information_schema.columns WHERE table_name = 'RequestAssignees' AND column_name = 'IsDeleted'")
        dtype = cursor.fetchone()[0]
        if dtype != 'boolean':
             # Drop default if exists (it should be 0)
            cursor.execute('ALTER TABLE public."RequestAssignees" ALTER COLUMN "IsDeleted" DROP DEFAULT')
            cursor.execute('ALTER TABLE public."RequestAssignees" ALTER COLUMN "IsDeleted" TYPE boolean USING (CASE WHEN "IsDeleted" = 0 THEN FALSE ELSE TRUE END)')
            cursor.execute('ALTER TABLE public."RequestAssignees" ALTER COLUMN "IsDeleted" SET DEFAULT FALSE')
            print("Converted.")
        else:
            print("Already boolean.")

        print("Recreating indexes with boolean WHERE clause...")
        cursor.execute('CREATE INDEX "IX_RequestAssignees_RequestId_RoleId" ON public."RequestAssignees" USING btree ("RequestId", "RoleId") WHERE ("IsDeleted" = false)')
        cursor.execute('CREATE UNIQUE INDEX "IX_RequestAssignees_RequestId_RoleId_AssigneeId" ON public."RequestAssignees" USING btree ("RequestId", "RoleId", "AssigneeId") WHERE ("IsDeleted" = false)')
        
        print("Done.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_table()
