import psycopg2
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.config import PG_CONFIG

logger = logging.getLogger(__name__)

class PostgresLogger:
    """
    Logger to save conversation history to PostgreSQL
    Designed to work alongside the existing JSON adapter
    """
    
    def __init__(self):
        self.db_config = PG_CONFIG.copy()
        # Ensure we point to the right DB
        self.db_config["database"] = "ai_insights"
        self.enabled = True
        
    def _get_connection(self):
        if not self.enabled:
            return None
            
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.autocommit = True
            return conn
        except Exception as e:
            # Downgrade to warning and disable to prevent log spam
            logger.warning(f"Failed to connect to PostgreSQL (logging disabled): {e}")
            self.enabled = False
            return None

    def log_conversation(self, 
                        user_id: int, 
                        conversation_id: str, 
                        query: str, 
                        response: str, 
                        agents_used: List[str], 
                        metadata: Dict[str, Any] = None):
        """
        Log a conversation turn to the database
        """
        if not self.enabled:
            return

        conn = self._get_connection()
        if not conn:
            return  # Fail silently/log only, don't crash the app
            
        try:
            with conn.cursor() as cur:
                sql = """
                INSERT INTO conversations 
                (id, user_id, conversation_id, query, response, agents_used, metadata, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Generate a Turn ID (or use metadata if provided)
                import uuid
                turn_id = str(uuid.uuid4())
                
                cur.execute(sql, (
                    turn_id,
                    user_id,
                    conversation_id,
                    query,
                    response,
                    agents_used,
                    json.dumps(metadata) if metadata else None,
                    datetime.now()
                ))
            
            logger.info(f"Saved conversation {conversation_id} to PostgreSQL")
            
        except Exception as e:
            logger.error(f"Error saving to PostgreSQL: {e}")
        finally:
            if conn:
                conn.close()

# Singleton
_pg_logger = None

def get_postgres_logger():
    global _pg_logger
    if _pg_logger is None:
        _pg_logger = PostgresLogger()
    return _pg_logger
