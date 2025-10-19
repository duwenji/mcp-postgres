"""
Database connection and operation management for PostgreSQL MCP Server
"""

import logging
import re
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
                version_result = cursor.fetchone()
                # RealDictCursorを使用しているので辞書として扱う
                if version_result and isinstance(version_result, dict):
                    version_str = version_result.get("version", "Unknown")
                else:
                    version_str = str(version_result) if version_result else "Unknown"
                logger.info(f"PostgreSQL version: {version_str}")
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

    def _validate_table_name(self, table_name: str) -> None:
        """Validate table name to prevent SQL injection"""
        import re

        # Allow only alphanumeric characters and underscores
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            raise DatabaseError(f"Invalid table name: {table_name}")

    def create_entity(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new entity (row) in the specified table

        Args:
            table_name: Name of the table
            data: Dictionary of column names and values

        Returns:
            Dictionary with operation result
        """
        self._validate_table_name(table_name)

        if not data:
            raise DatabaseError("No data provided for creation")

        columns = ", ".join(data.keys())
        placeholders = ", ".join([f"%({key})s" for key in data.keys()])
        query = (
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) "
            "RETURNING *"  # nosec
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
        self._validate_table_name(table_name)

        query = f"SELECT * FROM {table_name}"  # nosec
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
        self._validate_table_name(table_name)

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

        query = (
            f"UPDATE {table_name} SET {', '.join(set_clauses)} "
            f"WHERE {' AND '.join(where_clauses)} RETURNING *"  # nosec
        )

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
        self._validate_table_name(table_name)

        where_clauses = []
        params = {}

        for key, value in conditions.items():
            where_clauses.append(f"{key} = %({key})s")
            params[key] = value

        query = (
            f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)} "
            "RETURNING *"  # nosec
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

    def create_table(
        self, table_name: str, columns: List[Dict[str, Any]], if_not_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Create a new table in the database

        Args:
            table_name: Name of the table to create
            columns: List of column definitions
            if_not_exists: Create table only if it doesn't exist

        Returns:
            Dictionary with operation result
        """
        self._validate_table_name(table_name)

        if not columns:
            raise DatabaseError("No columns provided for table creation")

        # Build column definitions
        column_definitions = []
        for column in columns:
            name = column["name"]
            data_type = column["type"]

            # Validate column name
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
                raise DatabaseError(f"Invalid column name: {name}")

            definition = f"{name} {data_type}"

            # Add constraints
            if not column.get("nullable", True):
                definition += " NOT NULL"

            if column.get("primary_key", False):
                definition += " PRIMARY KEY"

            if column.get("unique", False):
                definition += " UNIQUE"

            if "default" in column:
                definition += f" DEFAULT {column['default']}"

            column_definitions.append(definition)

        # Build CREATE TABLE query
        if_exists_clause = "IF NOT EXISTS " if if_not_exists else ""
        query = (
            f"CREATE TABLE {if_exists_clause}{table_name} "
            f"({', '.join(column_definitions)})"  # nosec
        )

        try:
            self.connection.execute_query(query)
            return {
                "success": True,
                "message": f"Table {table_name} created successfully",
            }
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def alter_table(
        self, table_name: str, operations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Modify table structure

        Args:
            table_name: Name of the table to modify
            operations: List of operations to perform

        Returns:
            Dictionary with operation result
        """
        self._validate_table_name(table_name)

        if not operations:
            raise DatabaseError("No operations provided for table alteration")

        try:
            # Execute each operation in a transaction
            for operation in operations:
                op_type = operation["type"]
                column_name = operation["column_name"]

                # Validate column name
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", column_name):
                    raise DatabaseError(f"Invalid column name: {column_name}")

                if op_type == "add_column":
                    data_type = operation["data_type"]
                    nullable = operation.get("nullable", True)
                    default = operation.get("default")

                    query = (
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}"  # nosec
                    )
                    if not nullable:
                        query += " NOT NULL"
                    if default:
                        query += f" DEFAULT {default}"

                    self.connection.execute_query(query)

                elif op_type == "drop_column":
                    query = (
                        f"ALTER TABLE {table_name} DROP COLUMN {column_name}"  # nosec
                    )
                    self.connection.execute_query(query)

                elif op_type == "alter_column":
                    data_type = operation["data_type"]
                    nullable = operation.get("nullable")
                    default = operation.get("default")

                    query = (
                        f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                        f"TYPE {data_type}"  # nosec
                    )
                    self.connection.execute_query(query)

                    if nullable is not None:
                        if nullable:
                            query = (
                                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                                f"DROP NOT NULL"  # nosec
                            )
                        else:
                            query = (
                                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                                f"SET NOT NULL"  # nosec
                            )
                        self.connection.execute_query(query)

                    if default is not None:
                        if default == "":
                            query = (
                                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                                f"DROP DEFAULT"  # nosec
                            )
                        else:
                            query = (
                                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                                f"SET DEFAULT {default}"  # nosec
                            )
                        self.connection.execute_query(query)

                elif op_type == "rename_column":
                    new_column_name = operation["new_column_name"]
                    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", new_column_name):
                        raise DatabaseError(
                            f"Invalid new column name: {new_column_name}"
                        )

                    query = (
                        f"ALTER TABLE {table_name} RENAME COLUMN {column_name} "
                        f"TO {new_column_name}"  # nosec
                    )
                    self.connection.execute_query(query)

            return {
                "success": True,
                "message": f"Table {table_name} altered successfully",
            }

        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def drop_table(
        self, table_name: str, cascade: bool = False, if_exists: bool = True
    ) -> Dict[str, Any]:
        """
        Delete a table from the database

        Args:
            table_name: Name of the table to delete
            cascade: Also delete objects that depend on this table
            if_exists: Don't throw error if table doesn't exist

        Returns:
            Dictionary with operation result
        """
        self._validate_table_name(table_name)

        if_exists_clause = "IF EXISTS " if if_exists else ""
        cascade_clause = " CASCADE" if cascade else ""
        query = (
            f"DROP TABLE {if_exists_clause}{table_name}{cascade_clause}"  # nosec
        )

        try:
            self.connection.execute_query(query)
            return {
                "success": True,
                "message": f"Table {table_name} dropped successfully",
            }
        except DatabaseError as e:
            return {"success": False, "error": str(e)}
