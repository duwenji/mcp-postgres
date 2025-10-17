"""
Resource management for PostgreSQL MCP Server
"""

import logging
from typing import List, Dict, Any
from mcp import Resource

from .database import DatabaseManager, DatabaseError
from .config import load_config

logger = logging.getLogger(__name__)


class DatabaseResourceManager:
    """Manage database-related resources"""
    
    def __init__(self):
        self.config = load_config()
        self.db_manager = DatabaseManager(self.config.postgres)
    
    async def get_tables_resource(self) -> str:
        """Get tables list as resource content"""
        try:
            self.db_manager.connection.connect()
            result = self.db_manager.get_tables()
            self.db_manager.connection.disconnect()
            
            if result["success"]:
                tables = result["tables"]
                content = f"# Database Tables in {self.config.postgres.database}\n\n"
                content += f"Total tables: {len(tables)}\n\n"
                
                for table in tables:
                    content += f"- {table}\n"
                
                return content
            else:
                return f"Error retrieving tables: {result['error']}"
                
        except Exception as e:
            logger.error(f"Error in get_tables_resource: {e}")
            return f"Error retrieving tables: {str(e)}"
    
    async def get_table_schema_resource(self, table_name: str, schema: str = "public") -> str:
        """Get table schema as resource content"""
        try:
            self.db_manager.connection.connect()
            
            # Get table schema information
            query = """
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length,
                numeric_precision,
                numeric_scale
            FROM information_schema.columns 
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """
            
            columns = self.db_manager.connection.execute_query(query, (schema, table_name))
            
            # Get table constraints
            constraints_query = """
            SELECT 
                tc.constraint_name,
                tc.constraint_type,
                kcu.column_name
            FROM information_schema.table_constraints tc
            LEFT JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
                AND tc.table_name = kcu.table_name
            WHERE tc.table_schema = %s AND tc.table_name = %s
            ORDER BY tc.constraint_type, tc.constraint_name
            """
            
            constraints = self.db_manager.connection.execute_query(constraints_query, (schema, table_name))
            
            self.db_manager.connection.disconnect()
            
            # Format content
            content = f"# Table Schema: {schema}.{table_name}\n\n"
            
            # Columns section
            content += "## Columns\n\n"
            content += "| Column Name | Data Type | Nullable | Default | Max Length | Precision | Scale |\n"
            content += "|-------------|-----------|----------|---------|------------|-----------|-------|\n"
            
            for col in columns:
                content += f"| {col['column_name']} | {col['data_type']} | {col['is_nullable']} | {col['column_default'] or 'NULL'} | {col['character_maximum_length'] or '-'} | {col['numeric_precision'] or '-'} | {col['numeric_scale'] or '-'} |\n"
            
            content += "\n"
            
            # Constraints section
            if constraints:
                content += "## Constraints\n\n"
                content += "| Constraint Name | Type | Column |\n"
                content += "|-----------------|------|--------|\n"
                
                for constraint in constraints:
                    content += f"| {constraint['constraint_name']} | {constraint['constraint_type']} | {constraint['column_name'] or '-'} |\n"
            
            return content
            
        except Exception as e:
            logger.error(f"Error in get_table_schema_resource: {e}")
            return f"Error retrieving table schema: {str(e)}"
    
    async def get_database_info_resource(self) -> str:
        """Get database information as resource content"""
        try:
            self.db_manager.connection.connect()
            
            # Get database version
            version_result = self.db_manager.connection.execute_query("SELECT version();")
            version = version_result[0]["version"] if version_result else "Unknown"
            
            # Get database name and current user
            db_info_result = self.db_manager.connection.execute_query(
                "SELECT current_database(), current_user, current_schema();"
            )
            db_info = db_info_result[0] if db_info_result else {}
            
            # Get database size
            size_result = self.db_manager.connection.execute_query(
                "SELECT pg_size_pretty(pg_database_size(current_database())) as database_size;"
            )
            database_size = size_result[0]["database_size"] if size_result else "Unknown"
            
            # Get number of tables
            tables_count_result = self.db_manager.connection.execute_query(
                "SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';"
            )
            table_count = tables_count_result[0]["table_count"] if tables_count_result else 0
            
            self.db_manager.connection.disconnect()
            
            # Format content
            content = f"# Database Information\n\n"
            content += f"**Database Name**: {db_info.get('current_database', 'Unknown')}\n"
            content += f"**PostgreSQL Version**: {version}\n"
            content += f"**Current User**: {db_info.get('current_user', 'Unknown')}\n"
            content += f"**Current Schema**: {db_info.get('current_schema', 'Unknown')}\n"
            content += f"**Database Size**: {database_size}\n"
            content += f"**Table Count**: {table_count}\n"
            
            return content
            
        except Exception as e:
            logger.error(f"Error in get_database_info_resource: {e}")
            return f"Error retrieving database information: {str(e)}"


# Resource definitions
database_tables_resource = Resource(
    uri="database://tables",
    name="Database Tables",
    description="List of all tables in the database",
    mimeType="text/markdown"
)

database_info_resource = Resource(
    uri="database://info",
    name="Database Information",
    description="Database metadata and version information",
    mimeType="text/markdown"
)


def get_database_resources() -> List[Resource]:
    """Get all database resources"""
    return [
        database_tables_resource,
        database_info_resource,
    ]


def get_resource_handlers() -> Dict[str, callable]:
    """Get resource handlers"""
    resource_manager = DatabaseResourceManager()
    
    return {
        "database://tables": resource_manager.get_tables_resource,
        "database://info": resource_manager.get_database_info_resource,
    }


def get_table_schema_resource_handler() -> callable:
    """Get table schema resource handler factory"""
    resource_manager = DatabaseResourceManager()
    return resource_manager.get_table_schema_resource
