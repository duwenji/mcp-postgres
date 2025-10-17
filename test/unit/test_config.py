"""
Unit tests for configuration management
"""
import os
import pytest
from unittest.mock import patch

from src.config import PostgresConfig, ServerConfig, load_config, get_connection_string


class TestPostgresConfig:
    """Test PostgreSQL configuration"""
    
    def test_default_values(self):
        """Test default configuration values"""
        # Clear environment variables to test defaults
        with patch.dict(os.environ, {}, clear=True):
            config = PostgresConfig()
            
            assert config.host == "localhost"
            assert config.port == 5432  # Default port in config
            assert config.database == "postgres"
            assert config.username == "postgres"
            assert config.password == ""
            assert config.ssl_mode == "prefer"
            assert config.pool_size == 5
            assert config.max_overflow == 10
            assert config.connect_timeout == 30
    
    def test_custom_values(self):
        """Test configuration with custom values"""
        config = PostgresConfig(
            host="test-host",
            port=5433,
            database="test_db",
            username="test_user",
            password="test_pass",
            ssl_mode="require",
            pool_size=10,
            max_overflow=20,
            connect_timeout=60
        )
        
        assert config.host == "test-host"
        assert config.port == 5433
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.ssl_mode == "require"
        assert config.pool_size == 10
        assert config.max_overflow == 20
        assert config.connect_timeout == 60


class TestServerConfig:
    """Test MCP Server configuration"""
    
    def test_default_values(self):
        """Test default server configuration"""
        config = ServerConfig()
        
        assert config.log_level == "INFO"
        assert config.debug is False
        assert isinstance(config.postgres, PostgresConfig)
    
    def test_custom_values(self):
        """Test server configuration with custom values"""
        postgres_config = PostgresConfig(
            host="custom-host",
            database="custom_db"
        )
        
        config = ServerConfig(
            log_level="DEBUG",
            debug=True,
            postgres=postgres_config
        )
        
        assert config.log_level == "DEBUG"
        assert config.debug is True
        assert config.postgres.host == "custom-host"
        assert config.postgres.database == "custom_db"


class TestLoadConfig:
    """Test configuration loading"""
    
    @patch('dotenv.load_dotenv')
    def test_load_config_defaults(self, mock_load_dotenv):
        """Test loading configuration with defaults"""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'test-host',
            'POSTGRES_DB': 'test-db',
            'POSTGRES_USER': 'test-user'
        }, clear=True):
            print("DEBUG: Environment in test:", dict(os.environ))
            config = load_config()
            print("DEBUG: Loaded config:", config.postgres.dict())
            
            assert config.postgres.host == 'test-host'
            assert config.postgres.database == 'test-db'
            assert config.postgres.username == 'test-user'
            mock_load_dotenv.assert_called_once()
    
    @patch('dotenv.load_dotenv')
    def test_load_config_missing_required(self, mock_load_dotenv):
        """Test loading configuration with missing required fields"""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': '',
            'POSTGRES_DB': '',
            'POSTGRES_USER': ''
        }, clear=True):
            with pytest.raises(ValueError, match="POSTGRES_HOST environment variable is required"):
                load_config()
    
    @patch('dotenv.load_dotenv')
    def test_load_config_with_all_fields(self, mock_load_dotenv):
        """Test loading configuration with all fields"""
        with patch.dict(os.environ, {
            'POSTGRES_HOST': 'full-host',
            'POSTGRES_PORT': '5433',
            'POSTGRES_DB': 'full-db',
            'POSTGRES_USER': 'full-user',
            'POSTGRES_PASSWORD': 'full-pass',
            'POSTGRES_SSL_MODE': 'require',
            'POSTGRES_POOL_SIZE': '15',
            'POSTGRES_MAX_OVERFLOW': '25',
            'POSTGRES_CONNECT_TIMEOUT': '45',
            'MCP_LOG_LEVEL': 'WARNING',
            'MCP_DEBUG': 'true'
        }, clear=True):
            config = load_config()
            
            assert config.postgres.host == 'full-host'
            assert config.postgres.port == 5433
            assert config.postgres.database == 'full-db'
            assert config.postgres.username == 'full-user'
            assert config.postgres.password == 'full-pass'
            assert config.postgres.ssl_mode == 'require'
            assert config.postgres.pool_size == 15
            assert config.postgres.max_overflow == 25
            assert config.postgres.connect_timeout == 45
            assert config.log_level == 'WARNING'
            assert config.debug is True


class TestConnectionString:
    """Test connection string generation"""
    
    def test_basic_connection_string(self):
        """Test basic connection string without SSL"""
        config = PostgresConfig(
            host="localhost",
            port=5432,
            database="test_db",
            username="test_user",
            password="test_pass",
            ssl_mode="prefer"  # Explicitly set to default
        )
        
        conn_str = get_connection_string(config)
        expected = "postgresql://test_user:test_pass@localhost:5432/test_db"
        assert conn_str == expected
    
    def test_connection_string_with_ssl(self):
        """Test connection string with SSL mode"""
        config = PostgresConfig(
            host="secure-host",
            port=5432,
            database="secure_db",
            username="secure_user",
            password="secure_pass",
            ssl_mode="require"
        )
        
        conn_str = get_connection_string(config)
        expected = "postgresql://secure_user:secure_pass@secure-host:5432/secure_db?sslmode=require"
        assert conn_str == expected
    
    def test_connection_string_prefer_ssl(self):
        """Test connection string with prefer SSL mode (should not include sslmode)"""
        config = PostgresConfig(
            host="host",
            port=5432,
            database="db",
            username="user",
            password="pass",
            ssl_mode="prefer"  # Default, should not be included
        )
        
        conn_str = get_connection_string(config)
        expected = "postgresql://user:pass@host:5432/db"
        assert conn_str == expected
    
    def test_connection_string_empty_password(self):
        """Test connection string with empty password"""
        config = PostgresConfig(
            host="host",
            port=5432,
            database="db",
            username="user",
            password="",
            ssl_mode="prefer"  # Explicitly set to default
        )
        
        conn_str = get_connection_string(config)
        expected = "postgresql://user:@host:5432/db"
        assert conn_str == expected
