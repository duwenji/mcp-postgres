"""
Database connection and operation management for PostgreSQL MCP Server
"""

import logging
import re
import datetime
import decimal
import uuid
from typing import Any, Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from .config import PostgresConfig, get_connection_string

logger = logging.getLogger(__name__)


def convert_for_json_serialization(obj: Any) -> Any:
    """Convert Python objects to JSON serializable types"""
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    elif isinstance(obj, datetime.time):
        return obj.isoformat()
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, uuid.UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_for_json_serialization(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_for_json_serialization(item) for item in obj]
    return obj


def convert_for_database(obj: Any) -> Any:
    """
    Convert Python objects to PostgreSQL compatible types

    Args:
        obj: Python object to convert

    Returns:
        PostgreSQL compatible value
    """
    if isinstance(obj, (datetime.date, datetime.datetime)):
        return obj
    elif isinstance(obj, datetime.time):
        return obj
    elif isinstance(obj, decimal.Decimal):
        return obj
    elif isinstance(obj, uuid.UUID):
        return obj
    elif isinstance(obj, dict):
        # Convert dict to JSON string for PostgreSQL JSON/JSONB types
        import json

        return json.dumps(obj)
    elif isinstance(obj, list):
        # Convert list to JSON string for PostgreSQL array types
        import json

        return json.dumps(obj)
    elif isinstance(obj, str):
        # Check if string is a valid ISO date/datetime format
        try:
            # Try to parse as datetime
            return datetime.datetime.fromisoformat(obj.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            try:
                # Try to parse as date
                return datetime.date.fromisoformat(obj)
            except (ValueError, AttributeError):
                # Return as-is if not a date
                return obj
    return obj


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
                    converted_results = [
                        convert_for_json_serialization(dict(row)) for row in results
                    ]
                    return converted_results
                elif (
                    query.strip().upper().startswith("INSERT")
                    and "RETURNING" in query.upper()
                ):
                    # For INSERT with RETURNING clause, fetch the inserted row
                    results = cursor.fetchall()
                    self._connection.commit()
                    converted_results = [
                        convert_for_json_serialization(dict(row)) for row in results
                    ]
                    return converted_results
                elif (
                    query.strip().upper().startswith("UPDATE")
                    and "RETURNING" in query.upper()
                ):
                    # For UPDATE with RETURNING clause, fetch the updated row
                    results = cursor.fetchall()
                    self._connection.commit()
                    converted_results = [
                        convert_for_json_serialization(dict(row)) for row in results
                    ]
                    return converted_results
                elif (
                    query.strip().upper().startswith("DELETE")
                    and "RETURNING" in query.upper()
                ):
                    # For DELETE with RETURNING clause, fetch the deleted rows
                    results = cursor.fetchall()
                    self._connection.commit()
                    converted_results = [
                        convert_for_json_serialization(dict(row)) for row in results
                    ]
                    return converted_results
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
    """High-level database operations manager with connection pooling support"""

    def __init__(self, config: PostgresConfig):
        self.config = config
        self.connection = DatabaseConnection(config)
        self._is_connected = False

    def _validate_table_name(self, table_name: str) -> None:
        """Validate table name to prevent SQL injection"""
        import re

        # Allow only alphanumeric characters and underscores
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            raise DatabaseError(f"Invalid table name: {table_name}")

    def connect(self) -> None:
        """Establish database connection if not already connected"""
        if not self._is_connected:
            self.connection.connect()
            self._is_connected = True

    def disconnect(self) -> None:
        """Disconnect from database if connected"""
        if self._is_connected:
            self.connection.disconnect()
            self._is_connected = False

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

        # Convert data for database compatibility
        converted_data = {k: convert_for_database(v) for k, v in data.items()}

        columns = ", ".join(converted_data.keys())
        placeholders = ", ".join([f"%({key})s" for key in converted_data.keys()])
        query = (
            f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) "
            "RETURNING *"  # nosec
        )

        try:
            results = self.connection.execute_query(query, converted_data)
            return {"success": True, "created": results[0] if results else {}}
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def read_entity(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: Optional[str] = None,
        order_direction: str = "ASC",
        aggregate: Optional[str] = None,
        group_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Read entities from the specified table with optional conditions and advanced features

        Args:
            table_name: Name of the table
            conditions: Dictionary of WHERE conditions
            limit: Maximum number of rows to return
            offset: Number of rows to skip (for pagination)
            order_by: Column name to order by
            order_direction: Order direction (ASC or DESC)
            aggregate: Aggregate function (e.g., COUNT, SUM, AVG, MAX, MIN)
            group_by: Column name to group by

        Returns:
            Dictionary with query results
        """
        self._validate_table_name(table_name)

        # Build SELECT clause
        if aggregate:
            query = f"SELECT {aggregate} FROM {table_name}"  # nosec
        else:
            query = f"SELECT * FROM {table_name}"  # nosec

        params = {}

        # Build WHERE clause
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                where_clauses.append(f"{key} = %({key})s")
                params[key] = convert_for_database(value)
            query += " WHERE " + " AND ".join(where_clauses)

        # Build GROUP BY clause
        if group_by:
            query += f" GROUP BY {group_by}"

        # Build ORDER BY clause
        if order_by:
            if order_direction.upper() not in ["ASC", "DESC"]:
                order_direction = "ASC"
            query += f" ORDER BY {order_by} {order_direction}"

        # Build LIMIT and OFFSET clauses
        if limit > 0:
            query += f" LIMIT {limit}"
        if offset > 0:
            query += f" OFFSET {offset}"

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

        # Convert updates for database compatibility
        for key, value in updates.items():
            set_clauses.append(f"{key} = %(update_{key})s")
            params[f"update_{key}"] = convert_for_database(value)

        # Convert conditions for database compatibility
        where_clauses = []
        for key, value in conditions.items():
            where_clauses.append(f"{key} = %(condition_{key})s")
            params[f"condition_{key}"] = convert_for_database(value)

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

        # Convert conditions for database compatibility
        for key, value in conditions.items():
            where_clauses.append(f"{key} = %({key})s")
            params[key] = convert_for_database(value)

        query = (
            f"DELETE FROM {table_name} WHERE {' AND '.join(where_clauses)} "
            "RETURNING *"  # nosec
        )

        try:
            results = self.connection.execute_query(query, params)
            return {"success": True, "deleted": results, "affected_rows": len(results)}
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def batch_create_entities(
        self, table_name: str, data_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple entities in a single transaction

        Args:
            table_name: Name of the table
            data_list: List of dictionaries containing column names and values

        Returns:
            Dictionary with operation result
        """
        self._validate_table_name(table_name)

        if not data_list:
            raise DatabaseError("No data provided for batch creation")

        if len(data_list) > 1000:
            raise DatabaseError("Batch creation limited to 1000 entities per operation")

        # Use the first entity to determine column structure
        first_entity = data_list[0]
        columns = ", ".join(first_entity.keys())
        placeholders = ", ".join([f"%({key})s" for key in first_entity.keys()])

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders}) RETURNING *"  # nosec

        try:
            created_entities = []
            for data in data_list:
                # Convert data for database compatibility
                converted_data = {k: convert_for_database(v) for k, v in data.items()}
                results = self.connection.execute_query(query, converted_data)
                if results:
                    created_entities.append(results[0])

            return {
                "success": True,
                "created": created_entities,
                "count": len(created_entities),
            }
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def batch_update_entities(
        self,
        table_name: str,
        conditions_list: List[Dict[str, Any]],
        updates_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update multiple entities with different conditions and updates

        Args:
            table_name: Name of the table
            conditions_list: List of WHERE conditions for each entity
            updates_list: List of updates for each entity

        Returns:
            Dictionary with operation result
        """
        self._validate_table_name(table_name)

        if len(conditions_list) != len(updates_list):
            raise DatabaseError(
                "Conditions list and updates list must have the same length"
            )

        if len(conditions_list) > 100:
            raise DatabaseError("Batch update limited to 100 entities per operation")

        try:
            updated_entities = []
            total_affected = 0

            for conditions, updates in zip(conditions_list, updates_list):
                result = self.update_entity(table_name, conditions, updates)
                if result["success"]:
                    updated_entities.append(result["updated"])
                    total_affected += result.get("affected_rows", 0)

            return {
                "success": True,
                "updated": updated_entities,
                "affected_rows": total_affected,
                "count": len(updated_entities),
            }
        except DatabaseError as e:
            return {"success": False, "error": str(e)}

    def batch_delete_entities(
        self, table_name: str, conditions_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Delete multiple entities with different conditions

        Args:
            table_name: Name of the table
            conditions_list: List of WHERE conditions for each entity

        Returns:
            Dictionary with operation result
        """
        self._validate_table_name(table_name)

        if len(conditions_list) > 100:
            raise DatabaseError("Batch delete limited to 100 entities per operation")

        try:
            deleted_entities = []
            total_affected = 0

            for conditions in conditions_list:
                result = self.delete_entity(table_name, conditions)
                if result["success"]:
                    deleted_entities.extend(result["deleted"])
                    total_affected += result.get("affected_rows", 0)

            return {
                "success": True,
                "deleted": deleted_entities,
                "affected_rows": total_affected,
                "count": len(deleted_entities),
            }
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

                    query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type}"  # nosec
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
        query = f"DROP TABLE {if_exists_clause}{table_name}{cascade_clause}"  # nosec

        try:
            self.connection.execute_query(query)
            return {
                "success": True,
                "message": f"Table {table_name} dropped successfully",
            }
        except DatabaseError as e:
            return {"success": False, "error": str(e)}
