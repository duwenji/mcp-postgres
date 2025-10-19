"""
Database connection and operation management for PostgreSQL MCP Server
"""

import logging
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .config import PostgresConfig, get_connection_string

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations"""

    pass


class DatabaseConnection:
    """PostgreSQL database connection manager"""

    def __init__(self, config: PostgresConfig):
        self.config = config
        self.connection_string = get_connection_string(config)
        self._connection: Optional[psycopg2.extensions.connection] = None

    def connect(self) -> None:
        """Establish database connection"""
        try:
            self._connection = psycopg2.connect(
                self.connection_string, cursor_factory=RealDictCursor
            )
            logger.info(f"Connected to PostgreSQL database: {self.config.database}")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise DatabaseError(f"Database connection failed: {str(e)}")

    def disconnect(self) -> None:
        """Close database connection"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            logger.info("Disconnected from PostgreSQL database")

    def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results

        Args:
            query: SQL query to execute
            params: Query parameters for parameterized queries

        Returns:
            List of dictionaries representing query results

        Raises:
            DatabaseError: If query execution fails
        """
        if not self._connection or self._connection.closed:
            raise DatabaseError("Database connection is not established")

        try:
            with self._connection.cursor() as cursor:
                cursor.execute(query, params)

                # For SELECT queries, fetch results
                if query.strip().upper().startswith("SELECT"):
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                elif (
                    query.strip().upper().startswith("INSERT")
                    and "RETURNING" in query.upper()
                ):
                    # For INSERT with RETURNING clause, fetch the inserted row
                    results = cursor.fetchall()
                    self._connection.commit()
                    return [dict(row) for row in results]
                elif (
                    query.strip().upper().startswith("UPDATE")
                    and "RETURNING" in query.upper()
                ):
                    # For UPDATE with RETURNING clause, fetch the updated row
                    results = cursor.fetchall()
                    self._connection.commit()
                    return [dict(row) for row in results]
                elif (
                    query.strip().upper().startswith("DELETE")
                    and "RETURNING" in query.upper()
                ):
                    # For DELETE with RETURNING clause, fetch the deleted rows
                    results = cursor.fetchall()
                    self._connection.commit()
                    return [dict(row) for row in results]
                else:
                    # For other queries, commit and return affected row count
                    self._connection.commit()
                    return [{"affected_rows": cursor.rowcount}]

        except psycopg2.Error as e:
            self._connection.rollback()
            logger.error(f"Query execution failed: {e}")
            raise DatabaseError(f"Query execution failed: {str(e)}")

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self.connect()
            if self._connection is None:
                logger.error("Database connection is None")
                return False
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                logger.info(f"PostgreSQL version: {version['version']}")
            return True
        except (DatabaseError, psycopg2.Error) as e:
            logger.error(f"Connection test failed: {e}")
            return False
        finally:
            self.disconnect()


class DatabaseManager:
    """High-level database operations manager"""

    def __init__(self, config: PostgresConfig):
        self.config = config
        self.connection = DatabaseConnection(config)

    def create_entity(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity (row) in the specified table

        Args:
            table_name: Name of the table
            data: Dictionary of column names and values

        Returns:
            Dictionary with operation result
        """
        if not data:
            raise DatabaseError("No data provided for creation")

        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        query = (
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING *"
        )

        try:
            results = self.connection.execute_query(query, data)
            return {"success": True, "created": results[0] if results else {}}
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def read_entity(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        Read entities from the specified table with optional conditions

        Args:
            table_name: Name of the table
            conditions: Dictionary of WHERE conditions
            limit: Maximum number of rows to return

        Returns:
            Dictionary with query results
        """
        query = f"SELECT * FROM {table_name}"
        params = {}

        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f"{key} = %({key})s")
                params[key] = value
            query += " WHERE " + " AND ".join(where_clauses)

        query += f" LIMIT {limit}"

        try:
            results = self.connection.execute_query(query, params)
            return {"success": True, "results": results, "count": len(results)}
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def update_entity(
        self, table_name: str, conditions: Dict[str, Any], updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update entities in the specified table

        Args:
            table_name: Name of the table
            conditions: Dictionary of WHERE conditions
            updates: Dictionary of columns to update

        Returns:
            Dictionary with operation result
        """
        if not updates:
            raise DatabaseError("No updates provided")

        set_clauses = []
        params = {}

        for key, value in updates.items():
            set_clauses.append(f"{key} = %(update_{key})s")
            params[f"update_{key}"] = value

        where_clauses = []
        for key, value in conditions.items():
            where_clauses.append(f"{key} = %(condition_{key})s")
            params[f"condition_{key}"] = value

        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)} RETURNING *"

        try:
            results = self.connection.execute_query(query, params)
            return {
                "success": True,
                "updated": results[0] if results else {},
                "affected_rows": len(results),
            }
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def delete_entity(
        self, table_name: str, conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delete entities from the specified table

        Args:
            table_name: Name of the table
            conditions: Dictionary of WHERE conditions

        Returns:
            Dictionary with operation result
        """
        where_clauses = []
        params = {}

        for key, value in conditions.items():
            where_clauses.append(f"{key} = %({key})s")
            params[key] = value

        query = (
            f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)} RETURNING *"
        )

        try:
            results = self.connection.execute_query(query, params)
            return {"success": True, "deleted": results, "affected_rows": len(results)}
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def get_tables(self) -> Dict[str, Any]:
        """Get list of all tables in the database"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """

        try:
            results = self.connection.execute_query(query)
            table_names = [row["table_name"] for row in results]
            return {"success": True, "tables": table_names}
        except DatabaseError as e:
            return {"success": False, "error": str(e)}
