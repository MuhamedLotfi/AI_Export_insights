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
        
        with open("customer_view_test.txt", "w", encoding="utf-8") as f:
            f.write("--- vw_Customer_Project_Invoices (Top 5) ---\n")
            cur.execute("SELECT * FROM vw_Customer_Project_Invoices LIMIT 5;")
            colnames = [desc[0] for desc in cur.description]
            f.write(" | ".join(colnames) + "\n")
            rows = cur.fetchall()
            for row in rows:
                f.write(" | ".join([str(val) for val in row]) + "\n")
                
            f.write("\n--- vw_Supplier_Project_Invoices (Top 5) ---\n")
            cur.execute("SELECT * FROM vw_Supplier_Project_Invoices LIMIT 5;")
            colnames = [desc[0] for desc in cur.description]
            f.write(" | ".join(colnames) + "\n")
            rows = cur.fetchall()
            for row in rows:
                f.write(" | ".join([str(val) for val in row]) + "\n")
            
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
