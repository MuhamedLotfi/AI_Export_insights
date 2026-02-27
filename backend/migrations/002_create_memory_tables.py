"""
Migration 002 - Create Memory Management Tables
Creates session_summaries and user_preferences tables in ERP_AI database.
Uses existing conversations and feedback tables.
"""
import sys
import os
import psycopg2

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend.config import PG_CONFIG


def run_migration():
    print(f"--- Migration 002: Memory Management Tables ---")
    print(f"Database: {PG_CONFIG['database']} @ {PG_CONFIG['host']}:{PG_CONFIG['port']}")

    try:
        conn = psycopg2.connect(
            host=PG_CONFIG["host"],
            port=PG_CONFIG["port"],
            user=PG_CONFIG["user"],
            password=PG_CONFIG["password"],
            database=PG_CONFIG["database"]
        )
        conn.autocommit = True
        cur = conn.cursor()

        # ── 1. Session Summaries ──────────────────────────────────
        print("Creating table 'session_summaries'...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS session_summaries (
                id              SERIAL PRIMARY KEY,
                session_id      VARCHAR(255) NOT NULL UNIQUE,
                user_id         INTEGER NOT NULL,
                summary         TEXT NOT NULL,
                message_count   INTEGER DEFAULT 0,
                last_summarized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_session_summaries_session
                ON session_summaries (session_id);

            CREATE INDEX IF NOT EXISTS idx_session_summaries_user
                ON session_summaries (user_id);
        """)
        print("  -> session_summaries OK")

        # ── 2. User Preferences ───────────────────────────────────
        print("Creating table 'user_preferences'...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_preferences (
                id              SERIAL PRIMARY KEY,
                user_id         INTEGER NOT NULL,
                preference_key  VARCHAR(255) NOT NULL,
                preference_value TEXT NOT NULL,
                source          VARCHAR(50) DEFAULT 'inferred',
                confidence      FLOAT DEFAULT 0.5,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, preference_key)
            );

            CREATE INDEX IF NOT EXISTS idx_user_preferences_user
                ON user_preferences (user_id);
        """)
        print("  -> user_preferences OK")

        # ── 3. Verify existing tables ─────────────────────────────
        print("Verifying existing tables...")
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name IN ('conversations', 'feedback', 'session_summaries', 'user_preferences')
            ORDER BY table_name;
        """)
        found_tables = [row[0] for row in cur.fetchall()]
        print(f"  -> Found tables: {found_tables}")

        # Check conversations table has needed columns
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'conversations'
            ORDER BY ordinal_position;
        """)
        conv_cols = [row[0] for row in cur.fetchall()]
        print(f"  -> conversations columns: {conv_cols}")

        # Check feedback table
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'feedback'
            ORDER BY ordinal_position;
        """)
        fb_cols = [row[0] for row in cur.fetchall()]
        print(f"  -> feedback columns: {fb_cols}")

        print("\n=== Migration 002 completed successfully! ===")

        cur.close()
        conn.close()

    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] Connection failed: {e}")
        print(f"Check PG_CONFIG in backend/config.py")
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_migration()
