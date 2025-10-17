"""
Configuration management for PostgreSQL MCP Server
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class PostgresConfig(BaseSettings):
    """PostgreSQL connection configuration"""
    
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    database: str = Field(default="postgres", description="Database name")
    username: str = Field(default="postgres", description="Database username")
    password: str = Field(default="", description="Database password")
    
    # Connection options
    ssl_mode: str = Field(default="prefer", description="SSL mode")
    pool_size: int = Field(default=5, description="Connection pool size")
    max_overflow: int = Field(default=10, description="Maximum pool overflow")
    connect_timeout: int = Field(default=30, description="Connection timeout in seconds")
    
    class Config:
        env_prefix = "POSTGRES_"
        case_sensitive = False


class ServerConfig(BaseSettings):
    """MCP Server configuration"""
    
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # PostgreSQL configuration
    postgres: PostgresConfig = Field(default_factory=PostgresConfig)
    
    class Config:
        env_prefix = "MCP_"
        case_sensitive = False


def load_config() -> ServerConfig:
    """
    Load configuration from environment variables
    
    Returns:
        ServerConfig: Loaded configuration
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Load .env file if it exists
    from dotenv import load_dotenv
    load_dotenv()
    
    config = ServerConfig()
    
    # Validate required PostgreSQL configuration
    if not config.postgres.host:
        raise ValueError("POSTGRES_HOST environment variable is required")
    if not config.postgres.database:
        raise ValueError("POSTGRES_DB environment variable is required")
    if not config.postgres.username:
        raise ValueError("POSTGRES_USER environment variable is required")
    
    return config


def get_connection_string(config: PostgresConfig) -> str:
    """
    Generate PostgreSQL connection string from configuration
    
    Args:
        config: PostgreSQL configuration
        
    Returns:
        str: PostgreSQL connection string
    """
    base_conn_str = f"postgresql://{config.username}:{config.password}@{config.host}:{config.port}/{config.database}"
    
    # Add SSL mode if specified
    if config.ssl_mode and config.ssl_mode != "prefer":
        base_conn_str += f"?sslmode={config.ssl_mode}"
    
    return base_conn_str
