"""
Database Factory Module

Provides factory functions for creating database adapter instances
based on environment configuration.
"""

import os
import logging
from typing import Optional

from .database_adapter import DatabaseAdapter
from .postgresql_adapter import PostgreSQLAdapter

logger = logging.getLogger(__name__)


def create_database_adapter(database_type: str = None) -> DatabaseAdapter:
    """
    Create a database adapter instance based on configuration.
    
    Args:
        database_type: Type of database adapter to create.
                      If None, reads from DATABASE_TYPE environment variable.
    
    Returns:
        DatabaseAdapter: Configured database adapter instance.
    
    Raises:
        ValueError: If unsupported database type is specified.
        EnvironmentError: If required environment variables are missing.
    """
    if database_type is None:
        database_type = os.getenv('DATABASE_TYPE', 'postgresql')
    
    logger.info(f"Creating database adapter for type: {database_type}")
    
    if database_type == 'postgresql':
        # Get PostgreSQL configuration from environment
        # Check multiple environment variables in order of preference
        postgres_url = (
            os.getenv('POSTGRES_URL') or 
            os.getenv('DATABASE_CONNECTION_URL')
        )
        if not postgres_url:
            raise EnvironmentError(
                "Neither POSTGRES_URL nor DATABASE_CONNECTION_URL environment variable is set. "
                "Set one of these variables for PostgreSQL adapter. "
                "Format: postgresql://user:pass@host:port/dbname"
            )
        
        schema_prefix = os.getenv('SCHEMA_PREFIX', 'krai')
        
        logger.info(f"Creating PostgreSQL adapter with schema prefix: {schema_prefix}")
        
        return PostgreSQLAdapter(
            postgres_url=postgres_url,
            schema_prefix=schema_prefix
        )
    
    else:
        raise ValueError(f"Unsupported database type: {database_type}")


def get_database_config() -> dict:
    """
    Get current database configuration from environment.
    
    Returns:
        dict: Database configuration parameters.
    """
    return {
        'database_type': os.getenv('DATABASE_TYPE', 'postgresql'),
        'postgres_url': os.getenv('POSTGRES_URL'),
        'database_connection_url': os.getenv('DATABASE_CONNECTION_URL'),
        'schema_prefix': os.getenv('SCHEMA_PREFIX', 'krai'),
    }
