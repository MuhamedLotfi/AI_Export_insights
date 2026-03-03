"""
Data Adapter - Abstraction layer for data sources
Supports JSON files and PostgreSQL database with seamless switching
"""
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataAdapter(ABC):
    """Abstract base class for data adapters"""

    @abstractmethod
    def get_all(self, table: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_by_id(self, table: str, record_id: Any) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def query(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete(self, table: str, record_id: Any) -> bool:
        pass

    @abstractmethod
    def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, List[str]]:
        pass


class JSONDataAdapter(DataAdapter):
    """JSON file-based data adapter"""

    def __init__(self, data_dir: str, file_mapping: Dict[str, str]):
        self.data_dir = data_dir
        self.file_mapping = file_mapping
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._load_all_data()

    def _load_all_data(self):
        for table, filepath in self.file_mapping.items():
            self._load_table(table, filepath)

    def _load_table(self, table: str, filepath: str):
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._cache[table] = data if isinstance(data, list) else data.get('data', [])
                logger.info(f"Loaded {len(self._cache.get(table, []))} records from {table}")
            else:
                self._cache[table] = []
                logger.warning(f"File not found: {filepath}, initializing empty table: {table}")
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            self._cache[table] = []

    def _save_table(self, table: str):
        if table in self.file_mapping:
            filepath = self.file_mapping[table]
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({"data": self._cache.get(table, [])}, f, indent=2, default=str)
            except Exception as e:
                logger.error(f"Error saving {filepath}: {e}")

    def get_all(self, table: str) -> List[Dict[str, Any]]:
        return self._cache.get(table, [])

    def get_by_id(self, table: str, record_id: Any) -> Optional[Dict[str, Any]]:
        for record in self._cache.get(table, []):
            if record.get('id') == record_id:
                return record
        return None

    def query(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        records = self._cache.get(table, [])
        results = []
        for record in records:
            match = True
            for key, value in filters.items():
                if key not in record:
                    match = False
                    break
                if isinstance(value, dict):
                    if '$eq' in value and record[key] != value['$eq']:
                        match = False
                    elif '$ne' in value and record[key] == value['$ne']:
                        match = False
                    elif '$gt' in value and not (record[key] > value['$gt']):
                        match = False
                    elif '$gte' in value and not (record[key] >= value['$gte']):
                        match = False
                    elif '$lt' in value and not (record[key] < value['$lt']):
                        match = False
                    elif '$lte' in value and not (record[key] <= value['$lte']):
                        match = False
                    elif '$in' in value and record[key] not in value['$in']:
                        match = False
                    elif '$contains' in value and value['$contains'].lower() not in str(record[key]).lower():
                        match = False
                elif record[key] != value:
                    match = False
            if match:
                results.append(record)
        return results

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if table not in self._cache:
            self._cache[table] = []
        if 'id' not in data:
            existing_ids = [r.get('id', 0) for r in self._cache[table] if isinstance(r.get('id'), int)]
            data['id'] = max(existing_ids, default=0) + 1
        data['created_at'] = datetime.now().isoformat()
        self._cache[table].append(data)
        self._save_table(table)
        return data

    def update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        records = self._cache.get(table, [])
        for i, record in enumerate(records):
            if record.get('id') == record_id:
                records[i].update(data)
                records[i]['updated_at'] = datetime.now().isoformat()
                self._save_table(table)
                return records[i]
        return {}

    def delete(self, table: str, record_id: Any) -> bool:
        records = self._cache.get(table, [])
        for i, record in enumerate(records):
            if record.get('id') == record_id:
                del records[i]
                self._save_table(table)
                return True
        return False

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        sql = sql.strip().lower()
        results = []
        try:
            if sql.startswith('select'):
                from_match = sql.split('from')
                if len(from_match) < 2:
                    return []
                table_part = from_match[1].strip()
                table_name = table_part.split()[0].strip()
                results = list(self._cache.get(table_name, []))

                if 'where' in sql:
                    where_part = sql.split('where')[1]
                    if 'order by' in where_part:
                        where_part = where_part.split('order by')[0]
                    if 'limit' in where_part:
                        where_part = where_part.split('limit')[0]
                    results = self._apply_where(results, where_part.strip())

                if 'order by' in sql:
                    order_part = sql.split('order by')[1]
                    if 'limit' in order_part:
                        order_part = order_part.split('limit')[0]
                    order_col = order_part.strip().split()[0]
                    desc = 'desc' in order_part
                    results = sorted(results, key=lambda x: x.get(order_col, ''), reverse=desc)

                if 'limit' in sql:
                    limit_part = sql.split('limit')[1].strip()
                    limit_num = int(limit_part.split()[0])
                    results = results[:limit_num]

                select_part = from_match[0].replace('select', '').strip()
                if select_part != '*':
                    columns = [c.strip() for c in select_part.split(',')]
                    results = [{c: r.get(c) for c in columns if c in r} for r in results]
        except Exception as e:
            logger.error(f"Error executing query: {sql}, error: {e}")
        return results

    def _apply_where(self, records: List[Dict], where_clause: str) -> List[Dict]:
        filtered = []
        for record in records:
            try:
                condition = where_clause
                for col, val in record.items():
                    if col in condition:
                        if isinstance(val, str):
                            condition = condition.replace(col, f"'{val}'")
                        else:
                            condition = condition.replace(col, str(val))
                if '=' in condition and '>' not in condition and '<' not in condition:
                    parts = condition.split('=')
                    if len(parts) == 2:
                        left = parts[0].strip().strip("'")
                        right = parts[1].strip().strip("'")
                        if left == right:
                            filtered.append(record)
                else:
                    filtered.append(record)
            except:
                pass
        return filtered

    def get_schema(self) -> Dict[str, List[str]]:
        schema = {}
        for table, records in self._cache.items():
            if records:
                schema[table] = list(records[0].keys())
            else:
                schema[table] = []
        return schema

    def refresh(self, table: Optional[str] = None):
        if table:
            if table in self.file_mapping:
                self._load_table(table, self.file_mapping[table])
        else:
            self._load_all_data()


class DatabaseAdapter(DataAdapter):
    """
    PostgreSQL database adapter using SQLAlchemy.
    Provides live database access for the AI agent pipeline.
    """

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._engine = None
        self._init_engine()

    def _init_engine(self):
        """Initialize SQLAlchemy engine"""
        try:
            from backend.ai_agent.database_service import get_engine
            self._engine = get_engine()
            if self._engine:
                logger.info("DatabaseAdapter connected to PostgreSQL")
            else:
                logger.error("DatabaseAdapter: engine is None")
        except Exception as e:
            logger.error(f"DatabaseAdapter init error: {e}")

    def _ensure_engine(self):
        """Lazy re-init if engine was not available"""
        if self._engine is None:
            self._init_engine()
        return self._engine is not None

    def _serialize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize dict/list values to JSON strings for SQL compatibility"""
        import json
        serialized = {}
        for k, v in params.items():
            if isinstance(v, (dict, list)):
                serialized[k] = json.dumps(v, default=str)
            else:
                serialized[k] = v
        return serialized

    def get_schema(self) -> Dict[str, List[str]]:
        """Get all table names and their columns from the database"""
        import warnings
        schema = {}
        if not self._ensure_engine():
            return schema
        try:
            from sqlalchemy import inspect as sa_inspect
            inspector = sa_inspect(self._engine)
            for table_name in inspector.get_table_names():
                # Suppress pgvector 'vector' type warning (managed by vector_service.py)
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message="Did not recognize type 'vector'")
                    columns = inspector.get_columns(table_name)
                schema[table_name] = [col['name'] for col in columns]
            logger.info(f"Database schema loaded: {len(schema)} tables")
        except Exception as e:
            logger.error(f"Error fetching schema: {e}")
        return schema

    def get_all(self, table: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get all records from a table (with safety limit)"""
        if not self._ensure_engine():
            return []
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                result = conn.execute(text(f'SELECT * FROM "{table}" LIMIT :lim'), {"lim": limit})
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error in get_all({table}): {e}")
            return []

    def _get_pk_column(self, table: str) -> str:
        """Helper to get primary key column name based on table conventions"""
        # System tables use lowercase 'id'
        if table in ["users", "user_agents", "conversations", "feedback", "embeddings", "agents"]:
            return "id"
        # ERP legacy tables use PascalCase 'Id'
        return "Id"

    def get_by_id(self, table: str, record_id: Any) -> Optional[Dict[str, Any]]:
        """Get a single record by Id"""
        if not self._ensure_engine():
            return None
        try:
            from sqlalchemy import text
            pk_col = self._get_pk_column(table)
            
            with self._engine.connect() as conn:
                result = conn.execute(
                    text(f'SELECT * FROM "{table}" WHERE "{pk_col}" = :id LIMIT 1'),
                    {"id": record_id}
                )
                row = result.fetchone()
                return dict(row._mapping) if row else None
        except Exception as e:
            logger.error(f"Error in get_by_id({table}, {record_id}): {e}")
            return None

    def query(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query records with key=value filters"""
        if not self._ensure_engine():
            return []
        try:
            from sqlalchemy import text
            where_parts = []
            params = {}
            for i, (key, value) in enumerate(filters.items()):
                param_name = f"p{i}"
                # Handle ID column if it's passed in filters
                col_name = key
                if key.lower() == "id":
                    col_name = self._get_pk_column(table)
                
                if value is None:
                    where_parts.append(f'"{col_name}" IS NULL')
                else:
                    where_parts.append(f'"{col_name}" = :{param_name}')
                    params[param_name] = value

            where_clause = " AND ".join(where_parts) if where_parts else "TRUE"
            sql = f'SELECT * FROM "{table}" WHERE {where_clause} LIMIT 500'

            with self._engine.connect() as conn:
                result = conn.execute(text(sql), params)
                return [dict(row._mapping) for row in result]
        except Exception as e:
            logger.error(f"Error in query({table}): {e}")
            return []

    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a record into a table"""
        if not self._ensure_engine():
            return data
        try:
            from sqlalchemy import text
            # Serialize complex types (dict/list) to JSON strings
            safe_data = self._serialize_params(data)
            
            columns = ', '.join([f'"{k}"' for k in safe_data.keys()])
            placeholders = ', '.join([f':{k}' for k in safe_data.keys()])
            sql = f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders}) RETURNING *'

            with self._engine.connect() as conn:
                result = conn.execute(text(sql), safe_data)
                conn.commit()
                row = result.fetchone()
                return dict(row._mapping) if row else data
        except Exception as e:
            logger.error(f"Error in insert({table}): {e}")
            return data

    def update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a record by Id"""
        if not self._ensure_engine():
            return data
        try:
            from sqlalchemy import text
            pk_col = self._get_pk_column(table)
            
            # Serialize complex types
            safe_data = self._serialize_params(data)
            
            set_parts = [f'"{k}" = :{k}' for k in safe_data.keys()]
            set_clause = ', '.join(set_parts)
            safe_data['_id'] = record_id
            sql = f'UPDATE "{table}" SET {set_clause} WHERE "{pk_col}" = :_id RETURNING *'

            with self._engine.connect() as conn:
                result = conn.execute(text(sql), safe_data)
                conn.commit()
                row = result.fetchone()
                return dict(row._mapping) if row else data
        except Exception as e:
            logger.error(f"Error in update({table}, {record_id}): {e}")
            return data

    def delete(self, table: str, record_id: Any) -> bool:
        """Delete a record by Id"""
        if not self._ensure_engine():
            return False
        try:
            from sqlalchemy import text
            pk_col = self._get_pk_column(table)
            
            with self._engine.connect() as conn:
                result = conn.execute(
                    text(f'DELETE FROM "{table}" WHERE "{pk_col}" = :id'),
                    {"id": record_id}
                )
                conn.commit()
                return result.rowcount > 0
        except Exception as e:
            logger.error(f"Error in delete({table}, {record_id}): {e}")
            return False

    def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute raw SQL and return results"""
        if not self._ensure_engine():
            return []
        
        # Security check: Enforce READ-ONLY access
        # Remove comment blocks purely for validation
        import re
        sql_clean = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        sql_clean = re.sub(r'--.*?\n', '\n', sql_clean)
        
        sql_lower = sql_clean.strip().lower()
        if not (sql_lower.startswith("select") or sql_lower.startswith("with") or sql_lower.startswith("show") or sql_lower.startswith("explain")):
            logger.warning(f"Blocked non-SELECT query: {sql}")
            return []
            
        try:
            from sqlalchemy import text
            with self._engine.connect() as conn:
                result = conn.execute(text(sql), params or {})
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                conn.commit()
                return []
        except Exception as e:
            logger.error(f"Error executing SQL: {e}")
            return []

    def refresh(self, table: Optional[str] = None):
        """No-op for database adapter (always live)"""
        pass


def get_data_adapter() -> DataAdapter:
    """Factory function to get the appropriate data adapter"""
    from backend.config import DATA_SOURCE, JSON_FILES, DATA_DIR, PG_CONFIG

    if DATA_SOURCE == "json":
        return JSONDataAdapter(DATA_DIR, JSON_FILES)
    else:
        return DatabaseAdapter(PG_CONFIG)


# Global singleton instance
_data_adapter: Optional[DataAdapter] = None


def get_adapter() -> DataAdapter:
    """Get or create the global data adapter instance"""
    global _data_adapter
    if _data_adapter is None:
        _data_adapter = get_data_adapter()
    return _data_adapter
