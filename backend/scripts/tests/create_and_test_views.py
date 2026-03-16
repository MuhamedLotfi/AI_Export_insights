import psycopg2
import sys
import os

def main():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="ERP_AI",
            user="postgres",
            password="postgres_erp",
            port=5432
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Read the views sql file
        sql_file_path = r"d:\AI\AI_Export_insights\data\reports\00_core_views.sql"
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        print("Creating Views...")
        cur.execute(sql_script)
        print("Views created successfully!\n")
        
        print("--- Testing vw_Customer_Project_Invoices (Top 3 rows) ---")
        cur.execute('SELECT * FROM "vw_Customer_Project_Invoices" LIMIT 3;')
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        print(" | ".join(colnames))
        for row in rows:
            print(" | ".join([str(val) for val in row]))
            
        print("\n--- Testing vw_Supplier_Project_Invoices (Top 3 rows) ---")
        cur.execute('SELECT * FROM "vw_Supplier_Project_Invoices" LIMIT 3;')
        colnames = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        print(" | ".join(colnames))
        for row in rows:
            print(" | ".join([str(val) for val in row]))
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
