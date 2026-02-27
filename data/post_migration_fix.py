import psycopg2
import json

CONN_PARAMS = {
    "dbname": "ERP_AI", 
    "user": "postgres", 
    "password": "postgres_erp", 
    "host": "localhost"
}

JSON_FILE = r"D:\AI\AI_Export_insights\data\bit_columns.json"

def run_fix():
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        tables = json.load(f)
        
    try:
        conn = psycopg2.connect(**CONN_PARAMS)
        cursor = conn.cursor()
        
        for table, cols in tables.items():
            print(f"Fixing table {table}...")
            # Strip brackets if present (scan script captured content inside brackets? Let's check)
            # Scan script: m_table.group(1). so 'TableName'.
            # Col: 'ColName'.
            
            # Format: ALTER TABLE public."Table" ...
            # We need to construct SQL.
            
            # Note: Postgres tables created by migration script are quoted "Table".
            # So case sensitivity is preserved.
            
            # Some tables might have multiple bit columns.
            # ALTER TABLE t ALTER c1 TYPE boolean USING c1::boolean, ALTER c2 ...
            
            for col in cols:
                # Check current type
                cursor.execute("""
                    SELECT data_type, column_default 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                      AND table_name = %s 
                      AND column_name = %s
                """, (table, col))
                row = cursor.fetchone()
                if not row:
                    print(f"  Column {col} not found in {table}")
                    continue
                
                dtype, default_val = row
                
                if dtype == 'boolean':
                    print(f"  Column {col} is already boolean. Skipping.")
                    continue
                
                # Handle default value
                new_default = None
                if default_val is not None:
                    # default_val string e.g. "0" or "((0))"
                    if '1' in default_val:
                        new_default = 'TRUE'
                    elif '0' in default_val:
                        new_default = 'FALSE'
                    
                    # Drop default first
                    try:
                        cursor.execute(f'ALTER TABLE public."{table}" ALTER COLUMN "{col}" DROP DEFAULT')
                    except Exception as e:
                        print(f"  Error dropping default for {col}: {e}")
                
                # Convert type
                try:
                    cursor.execute(f'ALTER TABLE public."{table}" ALTER COLUMN "{col}" TYPE boolean USING (CASE WHEN "{col}" = 0 THEN FALSE ELSE TRUE END)')
                except Exception as e:
                    print(f"  Error converting {col}: {e}")
                    conn.rollback()
                    # If failed, try to restore default? (Implicit rollback handles it?)
                    # But we explicitly committed before loop? No.
                    # We commit PER TABLE.
                    continue

                # Restore default if needed
                if new_default:
                    try:
                        cursor.execute(f'ALTER TABLE public."{table}" ALTER COLUMN "{col}" SET DEFAULT {new_default}')
                    except Exception as e:
                        print(f"  Error setting default for {col}: {e}")
            
            conn.commit()
            print(f"  Processed {table}")
            
        conn.close()
        print("Boolean conversion finished.")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    run_fix()
