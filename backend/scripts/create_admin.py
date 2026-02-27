"""Create admin user directly using psycopg2 (no project imports needed)"""
import psycopg2
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password_hash = pwd_context.hash("admin123")

conn = psycopg2.connect(
    host="localhost", port=5432,
    database="ERP_AI",
    user="postgres", password="postgres_erp"
)
conn.autocommit = True
cur = conn.cursor()

# Create users table if not exists
cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        email VARCHAR(255),
        password_hash TEXT NOT NULL,
        role VARCHAR(50) DEFAULT 'user',
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT NOW()
    )
""")

# Check if admin exists
cur.execute("SELECT id FROM users WHERE username = 'admin'")
row = cur.fetchone()

if row:
    cur.execute("UPDATE users SET password_hash = %s, role = 'admin', is_active = TRUE WHERE username = 'admin'", (password_hash,))
    admin_id = row[0]
    print(f"Admin user updated (id={admin_id})")
else:
    cur.execute(
        "INSERT INTO users (username, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, %s) RETURNING id",
        ("admin", "admin@export-insights.com", password_hash, "admin", True)
    )
    admin_id = cur.fetchone()[0]
    print(f"Admin user created (id={admin_id})")

# Create user_agents table if not exists
cur.execute("""
    CREATE TABLE IF NOT EXISTS user_agents (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        agent_code VARCHAR(100) NOT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        granted_by INTEGER,
        granted_at TIMESTAMP DEFAULT NOW()
    )
""")

# Create conversations table if not exists
cur.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        conversation_id VARCHAR(255),
        query TEXT,
        response TEXT,
        agents_used JSONB,
        data JSONB,
        chart_data JSONB,
        insights JSONB,
        recommendations JSONB,
        timestamp TIMESTAMP DEFAULT NOW()
    )
""")

# Create feedback table if not exists
cur.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        message_id VARCHAR(255),
        rating VARCHAR(50),
        comment TEXT,
        timestamp TIMESTAMP DEFAULT NOW()
    )
""")

# Assign all domain agents to admin
agents = ["sales", "inventory", "purchasing", "accounting", "projects"]
for agent_code in agents:
    cur.execute("SELECT id FROM user_agents WHERE user_id = %s AND agent_code = %s", (admin_id, agent_code))
    if not cur.fetchone():
        cur.execute("INSERT INTO user_agents (user_id, agent_code, is_active) VALUES (%s, %s, TRUE)", (admin_id, agent_code))
        print(f"  Assigned agent: {agent_code}")

# Verify
cur.execute("SELECT id, username, email, role, is_active FROM users WHERE username = 'admin'")
user = cur.fetchone()
print(f"\n Admin user ready:")
print(f"   ID: {user[0]}")
print(f"   Username: {user[1]}")
print(f"   Email: {user[2]}")
print(f"   Role: {user[3]}")
print(f"   Active: {user[4]}")
print(f"   Password: admin123")

cur.execute("SELECT agent_code FROM user_agents WHERE user_id = %s", (admin_id,))
agent_list = [row[0] for row in cur.fetchall()]
print(f"   Agents: {agent_list}")

cur.close()
conn.close()
