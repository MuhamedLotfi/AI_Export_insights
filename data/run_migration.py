import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration for initial connection (default postgres/postgres)
# We use this to create the new DB and Role
INITIAL_DB = "postgres"
INITIAL_USER = "postgres"
INITIAL_PASSWORD = os.getenv("PG_PASSWORD", "Itco@123") # Try default 'postgres' first
HOST = "localhost"
PORT = "5432"

NEW_DB_NAME = "ERP_AI"
NEW_USER_PASSWORD = "postgres_erp"
SQL_FILE = r"D:\AI\AI_Export_insights\data\ERP_PostgreSQL.sql"

def get_connection(db_name, user, password):
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=HOST,
            port=PORT
        )
        return conn
    except psycopg2.Error as e:
        print(f"Connection failed: {e}")
        return None

def run_migration():
    print(f"Connecting to {INITIAL_DB}...")
    # Try connecting with default password
    conn = get_connection(INITIAL_DB, INITIAL_USER, INITIAL_PASSWORD)
    if not conn:
        print(f"Retrying with new password '{NEW_USER_PASSWORD}'...")
        conn = get_connection(INITIAL_DB, INITIAL_USER, NEW_USER_PASSWORD)
    
    if not conn:
        print("Could not connect to PostgreSQL. Please check credentials.")
        return

    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # 1. Update/Create User Role
    print("Setting up 'postgres' role...")
    # We can't use the DO block easily for everything, let's just run SQL commands directly for this part
    # explicitly to avoid partial transaction issues
    try:
        # Check if we can just alter
        cursor.execute(f"ALTER USER postgres WITH PASSWORD '{NEW_USER_PASSWORD}';")
        print("Updated postgres password.")
    except Exception as e:
        print(f"Error updating user (might already be set): {e}")

    # 2. Re-create Database (DROP IF EXISTS)
    print(f"Checking database {NEW_DB_NAME}...")
    try:
        # Check if exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{NEW_DB_NAME}'")
        if cursor.fetchone():
            print(f"Dropping existing database {NEW_DB_NAME}...")
            # Close existing connections
            cursor.execute(f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '{NEW_DB_NAME}' AND pid <> pg_backend_pid();")
            cursor.execute(f'DROP DATABASE "{NEW_DB_NAME}"')
            print("Database dropped.")
        
        cursor.execute(f'CREATE DATABASE "{NEW_DB_NAME}"')
        print(f"Database {NEW_DB_NAME} created.")
        
    except Exception as e:
        print(f"Error re-creating database: {e}")
        cursor.close()
        conn.close()
        return

    cursor.close()
    conn.close()

    # 3. Apply Schema to New Database
    print(f"Applying schema to {NEW_DB_NAME}...")
    
    conn_new = get_connection(NEW_DB_NAME, INITIAL_USER, NEW_USER_PASSWORD)
    if not conn_new:
        print("Failed to connect to new database.")
        return
        
    cursor_new = conn_new.cursor()
    
    # Create the helper function and cast explicitly
    print("Creating integer -> boolean cast...")
    try:
        cursor_new.execute("""
        CREATE OR REPLACE FUNCTION int_to_bool_helper(int) RETURNS boolean AS $$
        BEGIN
            IF $1 = 0 THEN RETURN false;
            ELSE RETURN true;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """)
        
        # Check if cast exists
        cursor_new.execute("SELECT 1 FROM pg_cast WHERE castsource = 'integer'::regtype AND casttarget = 'boolean'::regtype")
        if not cursor_new.fetchone():
            cursor_new.execute("CREATE CAST (integer AS boolean) WITH FUNCTION int_to_bool_helper(int) AS IMPLICIT;")
            print("Cast created.")
        else:
            print("Cast function created (cast already exists).")
        conn_new.commit()
    except Exception as e:
        conn_new.rollback()
        print(f"Error creating cast: {e}")
        return

    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        sql_content = f.read()

        
    # Remove the initial DO block and comments if they are at the top,
    # because we already handled user creation.
    # The script has a DO block at the start.
    # We can just run the whole thing? 
    # The DO block is safe to run again (idempotent).
    # But checking for commented out create database lines.
    
    # We'll rely on psycopg2 to execute the script in one go or split by statement?
    # Psycopg2 can execute a large block.
    
    try:
        cursor_new.execute(sql_content)
        conn_new.commit()
        print("Schema applied successfully.")
        with open("migration_success.log", "w") as f:
            f.write("Success")
    except Exception as e:
        conn_new.rollback()
        # Print error safe (encode/decode for console)
        try:
            print(f"Error applying schema: {str(e)}")
        except:
            print("Error applying schema (encoding error in print)")
            
        with open("migration_error.log", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n")
            if hasattr(e, 'pgerror'):
                f.write(f"PG Error: {e.pgerror}\n")
            if hasattr(e, 'diag'):
                f.write(f"Diag: {e.diag.message_primary}\n")
        
    cursor_new.close()
    conn_new.close()
    print("Migration finished.")

if __name__ == "__main__":
    run_migration()
