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

    cur = conn.cursor()
    cur.execute("SET session_replication_role = 'replica';")

    print("Reading SQL script...")
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Parsing lines...")
    statements = []
    current_insert = []

    lines = content.split('\n')
    for line in lines:
        sline = line.strip()
        if not current_insert:
            if sline.upper().startswith('INSERT INTO'):
                current_insert.append(line)
                # An insert line might be complete on the same line
                if sline.endswith(")") or sline.endswith(");") or sline.endswith("')") or sline.endswith("');"):
                    statements.append("\n".join(current_insert).strip())
                    current_insert = []
        else:
            current_insert.append(line)
            if sline.endswith(")") or sline.endswith(");") or sline.endswith("')") or sline.endswith("');"):
                statements.append("\n".join(current_insert).strip())
                current_insert = []

    insert_pattern = re.compile(r'INSERT\s+INTO\s+public\."([^"]+)"\s*\(([^)]+)\)\s*VALUES\s*(.*)', re.IGNORECASE | re.DOTALL)

    success_count = 0
    error_count = 0

    print(f"Found {len(statements)} INSERT statements.")
    
    error_log_path = "upsert_errors_fixed.log"
    with open(error_log_path, "w", encoding="utf-8") as err_log:
        for stmt in statements:
            if not stmt.upper().startswith('INSERT INTO'):
                continue

            match = insert_pattern.match(stmt)
            if not match:
                try:
                    cur.execute(stmt)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    err_log.write(f"Error: {e}\nQuery: {stmt}\n\n")
                continue

            table_name = match.group(1)
            columns_str = match.group(2)
            values_str = match.group(3)

            # Ensure we wrap newlines in queries cleanly 
            cols = [c.strip().strip('"') for c in columns_str.split(',')]
            pk_cols = pks_dict.get(table_name, [])

            upsert_q = stmt
            if pk_cols:
                pk_conflict = ', '.join(f'"{pk}"' for pk in pk_cols)
                update_set = ', '.join(f'"{col}"=EXCLUDED."{col}"' for col in cols if col not in pk_cols)
                if update_set:
                    upsert_q += f'\nON CONFLICT ({pk_conflict}) DO UPDATE SET {update_set};'
                else:
                    upsert_q += f'\nON CONFLICT ({pk_conflict}) DO NOTHING;'
            else:
                pass
                
            try:
                cur.execute(upsert_q)
                success_count += 1
            except Exception as e:
                error_count += 1
                err_log.write(f"Table {table_name} Error: {e}\nQuery: {upsert_q}\n\n")

    cur.close()
    conn.close()
    print(f"Finished. Success: {success_count}, Errors: {error_count}")

if __name__ == "__main__":
    run_upsert()
