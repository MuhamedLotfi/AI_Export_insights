import psycopg2

CONN_PARAMS = {
    "dbname": "ERP_AI", 
    "user": "postgres", 
    "password": "postgres_erp", 
    "host": "localhost"
}

try:
    conn = psycopg2.connect(**CONN_PARAMS)
    cursor = conn.cursor()
    
    cursor.execute("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'RequestAssignees'")
    print("Indexes:")
    for row in cursor.fetchall():
        print(row)
        
    cursor.execute("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'RequestAssignees'::regclass")
    print("Constraints:")
    for row in cursor.fetchall():
        print(row)
    
    # Test explicit function
    try:
        cursor.execute("SELECT int_to_bool_helper(1)")
        print(f"Function works: {cursor.fetchone()}")
    except Exception as e:
        print(f"Function failed: {e}")
        conn.rollback()

    # Test explicit cast syntax
    try:
        cursor.execute("SELECT CAST(1 AS boolean)")
        print("Explicit CAST(1 AS boolean) works.")
    except Exception as e:
        print(f"Explicit CAST failed: {e}")
        conn.rollback()
        
    # Try insert 1 (integer) again
    try:
        print("Attempting INSERT VALUES (1)...")
        cursor.execute("INSERT INTO test_bool VALUES (1);")
        print("Success: INSERT (1) worked.")
    except Exception as e:
        print(f"Failed INSERT: {e}")
        conn.rollback()

        
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")
