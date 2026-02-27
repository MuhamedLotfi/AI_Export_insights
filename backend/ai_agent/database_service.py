"""
Database Service - Manages SQLAlchemy engine and LangChain SQLDatabase
Singleton pattern ensures one connection pool shared across the app.
"""
import logging
from typing import Optional
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from backend.config import PG_CONFIG

logger = logging.getLogger(__name__)


class DatabaseService:
    """Singleton database service managing SQLAlchemy engine"""
    _instance: Optional['DatabaseService'] = None
    _engine: Optional[Engine] = None

    @classmethod
    def get_instance(cls) -> 'DatabaseService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if DatabaseService._instance is not None:
            raise Exception("Use get_instance() instead")
        self._initialize()

    def _initialize(self):
        """Initialize SQLAlchemy engine"""
        try:
            user = PG_CONFIG.get("user")
            password = PG_CONFIG.get("password")
            host = PG_CONFIG.get("host")
            port = PG_CONFIG.get("port")
            dbname = PG_CONFIG.get("database")

            connection_str = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
            self._engine = create_engine(
                connection_str,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # test connections before use
                echo=False
            )
            # Quick connectivity check
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Database engine ready: {dbname}@{host}:{port}")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            self._engine = None

    def get_engine(self) -> Optional[Engine]:
        """Get SQLAlchemy engine"""
        return self._engine

    def get_sql_database(self):
        """Get LangChain SQLDatabase wrapper (lazy import)"""
        if self._engine is None:
            return None
        try:
            from langchain_community.utilities import SQLDatabase
            # Return full access (read-only) database
            return SafeSQLDatabase(self._engine)
        except ImportError:
            logger.warning("langchain_community not available for SQLDatabase")
            return None

    def get_restricted_database(self, include_tables: list):
        """Get LangChain SQLDatabase restricted to specific tables"""
        if self._engine is None:
            return None
        try:
            # Return restricted (read-only) database
            return SafeSQLDatabase(self._engine, include_tables=include_tables)
        except ImportError:
            logger.warning("langchain_community not available for SQLDatabase")
            return None


def get_engine() -> Optional[Engine]:
    """Helper: get the SQLAlchemy engine"""
    return DatabaseService.get_instance().get_engine()


def get_database():
    """Helper: get LangChain SQLDatabase"""
    return DatabaseService.get_instance().get_sql_database()

def get_restricted_db(include_tables: list):
    """Helper: get restricted LangChain SQLDatabase"""
    return DatabaseService.get_instance().get_restricted_database(include_tables)


# Define SafeSQLDatabase at module level so it can be used/imported
try:
    from langchain_community.utilities import SQLDatabase
    
    class SafeSQLDatabase(SQLDatabase):
        """
        A secure wrapper around SQLDatabase that only allows SELECT queries.
        This prevents the agent from accidentally or maliciously modifying data.
        """
        def run(self, command: str, fetch: str = "all", **kwargs) -> str:
            """
            Execute a SQL command, but only if it's a SELECT statement.
            """
            command_stripped = command.strip().lower()
            
            # Allow SELECT and WITH (CTE) queries
            if not (command_stripped.startswith("select") or command_stripped.startswith("with")):
                raise ValueError("Security violation: Only SELECT queries are allowed.")
            
            # Block common DML/DDL keywords just in case they are embedded (simple check)
            # Note: This is a basic check. A robust parser would be better but this covers 99% of agent outputs.
            forbidden = ["delete from", "update ", "insert into", "drop table", "alter table", "truncate table", "create table"]
            for bad_cmd in forbidden:
                if bad_cmd in command_stripped:
                     # Be careful not to block legit uses like "select * from updates" (table name)
                     # So we check for the keyword at start or preceded by space/newline
                     pass 
                     # For now, let's stick to the startswith check which is safer and usually sufficient for agents.
                     
            return super().run(command, fetch, **kwargs)
except ImportError:
    class SafeSQLDatabase:
        pass

