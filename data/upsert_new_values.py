import os
import psycopg2
import re

DB_NAME = "ERP_AI"
DB_USER = "postgres"
DB_PASS = os.getenv("PG_PASSWORD", "postgres_erp")
DB_HOST = "localhost"
DB_PORT = "5432"

SQL_FILE = r"D:\AI\AI_Export_insights\data\ERP2202_PostgreSQL.sql"

def get_pks(conn):
    cur = conn.cursor()
    # Query to get primary keys for all tables in public schema
    cur.execute("""
        SELECT tc.table_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name 
          AND tc.table_schema = kcu.table_schema
        WHERE tc.table_schema = 'public' 
          AND tc.constraint_type = 'PRIMARY KEY';
    """)
    pks = {}
    for row in cur.fetchall():
        table_name = row[0]
        col_name = row[1]
        if table_name not in pks:
            pks[table_name] = []
        pks[table_name].append(col_name)
    cur.close()
    return pks

def run_upsert():
    print(f"Connecting to {DB_NAME}...")
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT)
        conn.autocommit = True
    except psycopg2.Error as e:
        print(f"Connection failed: {e}")
        return

    pks_dict = get_pks(conn)
    print(f"Fetched PKs for {len(pks_dict)} tables.")
    
    cur = conn.cursor()
    
    # Create integer -> boolean cast if it doesn't exist
    try:
        cur.execute("""
        CREATE OR REPLACE FUNCTION int_to_bool_helper(int) RETURNS boolean AS $$
        BEGIN
            IF $1 = 0 THEN RETURN false;
            ELSE RETURN true;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """)
        # We catch exceptions for CREATE CAST as it might already exist
        cur.execute("SELECT 1 FROM pg_cast WHERE castsource = 'integer'::regtype AND casttarget = 'boolean'::regtype")
        if not cur.fetchone():
            cur.execute("CREATE CAST (integer AS boolean) WITH FUNCTION int_to_bool_helper(int) AS IMPLICIT;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Failed to create cast: {e}")
        
    print("Reading SQL script...")
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    insert_pattern = re.compile(r'INSERT INTO public\."([^"]+)"\s*\(([^)]+)\)\s*VALUES\s*(.*)', re.IGNORECASE)
    
    success_count = 0
    error_count = 0
    line_count = 0
    total_inserts = sum(1 for line in lines if line.strip().upper().startswith('INSERT INTO'))
    print(f"Found {total_inserts} INSERT statements.")

    # Disable foreign key checks for the session
    cur.execute("SET session_replication_role = 'replica';")

    error_log_path = "upsert_errors.log"
    with open(error_log_path, "w", encoding="utf-8") as err_log:
        for line in lines:
            line_count += 1
            sline = line.strip()
            if not sline.upper().startswith('INSERT INTO'):
                continue
                
            if sline.endswith(';'):
                sline = sline[:-1]
                
            match = insert_pattern.match(sline)
            if not match:
                try:
                    cur.execute(sline)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    err_log.write(f"Line {line_count} Error: {e}\nQuery: {sline}\n\n")
                    if error_count < 5:
                        print(f"Error on line {line_count}: {e}")
                continue

            table_name = match.group(1)
            columns_str = match.group(2)
            values_str = match.group(3)
            
            cols = [c.strip().strip('"') for c in columns_str.split(',')]
            pk_cols = pks_dict.get(table_name, [])
            
            upsert_q = sline
            if pk_cols:
                pk_conflict = ', '.join(f'"{pk}"' for pk in pk_cols)
                # Find columns that are not PKs to update
                update_set = ', '.join(f'"{col}"=EXCLUDED."{col}"' for col in cols if col not in pk_cols)
                
                if update_set:
                    upsert_q += f' ON CONFLICT ({pk_conflict}) DO UPDATE SET {update_set}'
                else:
                    upsert_q += f' ON CONFLICT ({pk_conflict}) DO NOTHING'
            else:
                # If no PK, we might get duplicates, could try to insert anyway
                pass
                
            try:
                cur.execute(upsert_q)
                success_count += 1
            except Exception as e:
                error_count += 1
                err_log.write(f"Table {table_name} Error: {e}\nQuery: {upsert_q}\n\n")
                if error_count < 10:
                    print(f"Error executing upsert on {table_name}: {e}")
                    print(f"Query: {upsert_q[:100]}...")
            
            if success_count % 500 == 0:
                print(f"Processed {success_count} inserts...")
                
    cur.close()
    conn.close()
    print(f"Finished. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    run_upsert()
