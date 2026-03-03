import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_conversations_table():
    """Add message_id and feedback columns to conversations table"""
    try:
        conn = psycopg2.connect(
            host="localhost", port=5432,
            database="ERP_AI",
            user="postgres", password="postgres_erp"
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Add message_id column
        cur.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS message_id VARCHAR(255);")
        # Ensure message_id is unique
        try:
            cur.execute("ALTER TABLE conversations ADD CONSTRAINT unique_message_id UNIQUE(message_id);")
        except Exception as e:
            if "already exists" not in str(e):
                logger.warning(f"Could not add unique constraint constraint: {e}")
        
        # Add feedback column
        cur.execute("ALTER TABLE conversations ADD COLUMN IF NOT EXISTS feedback VARCHAR(50);")
        
        logger.info("Successfully added message_id and feedback columns to conversations table.")

        # Update existing records to have a message_id to prevent null issues if needed later
        # We can just generate simple ones for historical data if missing
        cur.execute("UPDATE conversations SET message_id = 'msg_' || id::text WHERE message_id IS NULL;")
        
        logger.info("Populated historical records with message_id.")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_conversations_table()
