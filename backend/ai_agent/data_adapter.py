"""
Data Adapter - Abstraction layer for data sources
Supports JSON files and database with seamless switching
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
        """Get all records from a table/collection"""
        pass
    
    @abstractmethod
    def get_by_id(self, table: str, record_id: Any) -> Optional[Dict[str, Any]]:
        """Get a single record by ID"""
        pass
    
    @abstractmethod
    def query(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query records with filters"""
        pass
    
    @abstractmethod
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a new record"""
        pass
    
    @abstractmethod
    def update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record"""
        pass
    
    @abstractmethod
    def delete(self, table: str, record_id: Any) -> bool:
        """Delete a record"""
        pass
    
    @abstractmethod
    def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute a SQL-like query on the data"""
        pass


class JSONDataAdapter(DataAdapter):
    """JSON file-based data adapter"""
    
    def __init__(self, data_dir: str, file_mapping: Dict[str, str]):
        """
        Initialize JSON data adapter
        Args:
            data_dir: Directory containing JSON files
            file_mapping: Mapping of table names to file paths
        """
        self.data_dir = data_dir
        self.file_mapping = file_mapping
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._load_all_data()
    
    def _load_all_data(self):
        """Load all JSON files into memory"""
        for table, filepath in self.file_mapping.items():
            self._load_table(table, filepath)
    
    def _load_table(self, table: str, filepath: str):
        """Load a single JSON file"""
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
        """Save a table back to JSON file"""
        if table in self.file_mapping:
            filepath = self.file_mapping[table]
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({"data": self._cache.get(table, [])}, f, indent=2, default=str)
                logger.info(f"Saved {table} to {filepath}")
            except Exception as e:
                logger.error(f"Error saving {filepath}: {e}")
    
    def get_all(self, table: str) -> List[Dict[str, Any]]:
        """Get all records from a table"""
        return self._cache.get(table, [])
    
    def get_by_id(self, table: str, record_id: Any) -> Optional[Dict[str, Any]]:
        """Get a single record by ID"""
        records = self._cache.get(table, [])
        for record in records:
            if record.get('id') == record_id:
                return record
        return None
    
    def query(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query records with filters"""
        records = self._cache.get(table, [])
        results = []
        
        for record in records:
            match = True
            for key, value in filters.items():
                if key not in record:
                    match = False
                    break
                
                # Handle different filter operators
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
        """Insert a new record"""
        if table not in self._cache:
            self._cache[table] = []
        
        # Generate ID if not provided
        if 'id' not in data:
            existing_ids = [r.get('id', 0) for r in self._cache[table] if isinstance(r.get('id'), int)]
            data['id'] = max(existing_ids, default=0) + 1
        
        # Add timestamp
        data['created_at'] = datetime.now().isoformat()
        
        self._cache[table].append(data)
        self._save_table(table)
        return data
    
    def update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record"""
        records = self._cache.get(table, [])
        for i, record in enumerate(records):
            if record.get('id') == record_id:
                records[i].update(data)
                records[i]['updated_at'] = datetime.now().isoformat()
                self._save_table(table)
                return records[i]
        return {}
    
    def delete(self, table: str, record_id: Any) -> bool:
        """Delete a record"""
        records = self._cache.get(table, [])
        for i, record in enumerate(records):
            if record.get('id') == record_id:
                del records[i]
                self._save_table(table)
                return True
        return False
    
    def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL-like query on the cached data
        Supports basic SELECT, WHERE, ORDER BY, LIMIT
        """
        sql = sql.strip().lower()
        results = []
        
        try:
            # Parse SELECT ... FROM table
            if sql.startswith('select'):
                # Extract table name
                from_match = sql.split('from')
                if len(from_match) < 2:
                    return []
                
                table_part = from_match[1].strip()
                table_name = table_part.split()[0].strip()
                
                # Get base data
                results = list(self._cache.get(table_name, []))
                
                # Handle WHERE clause
                if 'where' in sql:
                    where_part = sql.split('where')[1]
                    if 'order by' in where_part:
                        where_part = where_part.split('order by')[0]
                    if 'limit' in where_part:
                        where_part = where_part.split('limit')[0]
                    
                    # Parse simple conditions
                    results = self._apply_where(results, where_part.strip())
                
                # Handle ORDER BY
                if 'order by' in sql:
                    order_part = sql.split('order by')[1]
                    if 'limit' in order_part:
                        order_part = order_part.split('limit')[0]
                    
                    order_col = order_part.strip().split()[0]
                    desc = 'desc' in order_part
                    results = sorted(results, key=lambda x: x.get(order_col, ''), reverse=desc)
                
                # Handle LIMIT
                if 'limit' in sql:
                    limit_part = sql.split('limit')[1].strip()
                    limit_num = int(limit_part.split()[0])
                    results = results[:limit_num]
                
                # Handle column selection
                select_part = from_match[0].replace('select', '').strip()
                if select_part != '*':
                    columns = [c.strip() for c in select_part.split(',')]
                    results = [{c: r.get(c) for c in columns if c in r} for r in results]
        
        except Exception as e:
            logger.error(f"Error executing query: {sql}, error: {e}")
        
        return results
    
    def _apply_where(self, records: List[Dict], where_clause: str) -> List[Dict]:
        """Apply WHERE clause filtering"""
        filtered = []
        
        for record in records:
            # Handle simple conditions: column = value, column > value, etc.
            try:
                # Replace SQL operators
                condition = where_clause
                for col, val in record.items():
                    if col in condition:
                        if isinstance(val, str):
                            condition = condition.replace(col, f"'{val}'")
                        else:
                            condition = condition.replace(col, str(val))
                
                # Evaluate (simplified - production would use proper parser)
                if '=' in condition and '>' not in condition and '<' not in condition:
                    parts = condition.split('=')
                    if len(parts) == 2:
                        left = parts[0].strip().strip("'")
                        right = parts[1].strip().strip("'")
                        if left == right:
                            filtered.append(record)
                else:
                    filtered.append(record)  # Fallback
            except:
                pass
        
        return filtered
    
    def get_schema(self) -> Dict[str, List[str]]:
        """Get schema information (table -> columns)"""
        schema = {}
        for table, records in self._cache.items():
            if records:
                schema[table] = list(records[0].keys())
            else:
                schema[table] = []
        return schema
    
    def refresh(self, table: Optional[str] = None):
        """Refresh data from files"""
        if table:
            if table in self.file_mapping:
                self._load_table(table, self.file_mapping[table])
        else:
            self._load_all_data()


class DatabaseAdapter(DataAdapter):
    """
    Database adapter for PostgreSQL
    Implements the same interface as JSONDataAdapter for seamless switching
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self._connection = None
        # TODO: Implement database connection
        logger.info("DatabaseAdapter initialized (placeholder - use JSON for now)")
    
    def get_all(self, table: str) -> List[Dict[str, Any]]:
        # TODO: Implement database query
        return []
    
    def get_by_id(self, table: str, record_id: Any) -> Optional[Dict[str, Any]]:
        # TODO: Implement
        return None
    
    def query(self, table: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        # TODO: Implement
        return []
    
    def insert(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implement
        return data
    
    def update(self, table: str, record_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implement
        return data
    
    def delete(self, table: str, record_id: Any) -> bool:
        # TODO: Implement
        return False
    
    def execute_query(self, sql: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        # TODO: Implement
        return []


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
