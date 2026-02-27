"""Create agents table and populate with initial data"""
import psycopg2
import json

# Connection settings
HOST = "localhost"
PORT = 5432
DB = "ERP_AI"
USER = "postgres"
PASS = "postgres_erp"

DOMAIN_AGENTS = {
    "sales": {
        "name": "Sales Analytics Agent",
        "description": "Analyzes sales data, revenue trends, and customer behavior",
        "icon": "trending_up",
        "tables": ["sales", "items", "project_59"],
        "keywords": ["sales", "revenue", "sold", "customer", "top items", "project", "contract", "opportunity"],
    },
    "inventory": {
        "name": "Inventory Management Agent",
        "description": "Monitors stock levels, reorder points, and warehouse operations",
        "icon": "inventory_2",
        "tables": ["inventory", "items"],
        "keywords": ["inventory", "stock", "warehouse", "reorder", "quantity"],
    },
    "purchasing": {
        "name": "Purchasing Agent",
        "description": "Manages vendor analysis, purchase orders, and procurement",
        "icon": "shopping_cart",
        "tables": ["purchasing", "vendors", "project_59"],
        "keywords": ["purchase", "vendor", "supplier", "lead time", "order"],
    },
    "accounting": {
        "name": "Accounting Agent",
        "description": "Handles financial analysis, costs, margins, and profitability",
        "icon": "account_balance",
        "tables": ["items", "costs", "project_59"],
        "keywords": ["cost", "margin", "profit", "pricing", "financial"],
    },
    "projects": {
        "name": "Project Analytics Agent",
        "description": "Tracks project performance, status, and profitability",
        "icon": "assignment",
        "tables": ["project_59", "sales", "purchasing"],
        "keywords": ["project", "status", "profitability", "completion", "contract"],
    },
}

conn = psycopg2.connect(
    host=HOST, port=PORT, database=DB, user=USER, password=PASS
)
conn.autocommit = True
cur = conn.cursor()

print("Creating 'agents' table...")
cur.execute("""
    CREATE TABLE IF NOT EXISTS agents (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        icon VARCHAR(50),
        capabilities JSONB,
        tables JSONB,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

print("Populating agents...")
for code, info in DOMAIN_AGENTS.items():
    cur.execute("SELECT id FROM agents WHERE code = %s", (code,))
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO agents (code, name, description, icon, capabilities, tables, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        """, (
            code, 
            info["name"], 
            info["description"], 
            info["icon"], 
            json.dumps(info.get("keywords", [])),
            json.dumps(info.get("tables", []))
        ))
        print(f"  Added agent: {code}")
    else:
        print(f"  Agent exists: {code}")

print("Done.")
cur.close()
conn.close()
