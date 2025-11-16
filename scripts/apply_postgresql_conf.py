#!/usr/bin/env python3
"""
Script to apply custom PostgreSQL configuration to running Docker container
"""

import os
import sys
import logging
import tempfile
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def apply_custom_config():
    """Apply custom PostgreSQL configuration to running container"""

    # Get the path to our custom postgresql.conf
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    custom_conf_path = os.path.join(
        current_dir, "src", "mcp_postgres_duwenji", "assets", "postgresql.conf"
    )

    if not os.path.exists(custom_conf_path):
        logger.error(f"Custom config file not found: {custom_conf_path}")
        return False

    # Check if container is running
    try:
        result = subprocess.run(
            [
                "docker",
                "ps",
                "--filter",
                "name=mcp-postgres-auto",
                "--format",
                "{{.Names}}",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        if "mcp-postgres-auto" not in result.stdout:
            logger.error("Container 'mcp-postgres-auto' is not running")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check container status: {e}")
        return False

    # Copy config file to container
    try:
        # Create a temporary copy of the config file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".conf", delete=False
        ) as temp_file:
            with open(custom_conf_path, "r") as source_file:
                temp_file.write(source_file.read())
            temp_conf_path = temp_file.name

        # Copy to container
        subprocess.run(
            [
                "docker",
                "cp",
                temp_conf_path,
                "mcp-postgres-auto:/var/lib/postgresql/data/postgresql.conf",
            ],
            check=True,
        )

        # Clean up temp file
        os.unlink(temp_conf_path)

        logger.info("Successfully applied custom PostgreSQL configuration")

        # Reload PostgreSQL configuration
        subprocess.run(
            [
                "docker",
                "exec",
                "mcp-postgres-auto",
                "psql",
                "-U",
                "postgres",
                "-c",
                "SELECT pg_reload_conf();",
            ],
            check=True,
        )

        logger.info("PostgreSQL configuration reloaded successfully")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to apply configuration: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


def check_current_config():
    """Check current PostgreSQL configuration"""
    try:
        # Get current slow query threshold
        result = subprocess.run(
            [
                "docker",
                "exec",
                "mcp-postgres-auto",
                "psql",
                "-U",
                "postgres",
                "-t",
                "-c",
                "SHOW log_min_duration_statement;",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        slow_query_threshold = result.stdout.strip()
        logger.info(f"Current slow query threshold: {slow_query_threshold}")

        # Check if auto_explain is loaded
        result = subprocess.run(
            [
                "docker",
                "exec",
                "mcp-postgres-auto",
                "psql",
                "-U",
                "postgres",
                "-t",
                "-c",
                "SHOW shared_preload_libraries;",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        shared_libraries = result.stdout.strip()
        logger.info(f"Shared preload libraries: {shared_libraries}")

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check configuration: {e}")
        return False


if __name__ == "__main__":
    logger.info("Applying custom PostgreSQL configuration...")

    if apply_custom_config():
        logger.info("Configuration applied successfully")
        logger.info("Checking current configuration...")
        check_current_config()
    else:
        logger.error("Failed to apply configuration")
        sys.exit(1)
