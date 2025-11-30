"""
Database Adapter Factory

Factory pattern for creating database adapters based on configuration.
Supports PostgreSQL database backend.
Note: Docker PostgreSQL is now handled by postgresql type with environment-based defaults.
"""

import os
import logging
from typing import Optional
from urllib.parse import urlparse, urlunparse

from .database_adapter import DatabaseAdapter


logger = logging.getLogger("krai.database.factory")


def create_database_adapter(
    database_type: Optional[str] = None,
    postgres_url: Optional[str] = None,
    postgres_host: Optional[str] = None,
    postgres_port: Optional[int] = None,
    postgres_db: Optional[str] = None,
    postgres_user: Optional[str] = None,
    postgres_password: Optional[str] = None,
    schema_prefix: Optional[str] = None
) -> DatabaseAdapter:
    """
    Create a database adapter based on the specified type.
    
    Args:
        database_type: Type of database adapter ('postgresql')
                      If None, reads from DATABASE_TYPE environment variable (default: 'postgresql')
        postgres_url: PostgreSQL connection URL (for PostgreSQL adapter)
        postgres_host: PostgreSQL host (alternative to postgres_url)
        postgres_port: PostgreSQL port (alternative to postgres_url)
        postgres_db: PostgreSQL database name (alternative to postgres_url)
        postgres_user: PostgreSQL user (alternative to postgres_url)
        postgres_password: PostgreSQL password (alternative to postgres_url)
        schema_prefix: Schema prefix for PostgreSQL (default: 'krai')
    
    Returns:
        DatabaseAdapter: Configured database adapter instance
    
    Raises:
        ValueError: If database_type is invalid or required configuration is missing
        ImportError: If required dependencies for the adapter are not installed
    
    Environment Variables:
        DATABASE_TYPE: Type of database adapter (default: 'postgresql')
        DATABASE_CONNECTION_URL or POSTGRES_URL: PostgreSQL connection URL
        POSTGRES_HOST: PostgreSQL host
        POSTGRES_PORT: PostgreSQL port
        POSTGRES_DB: PostgreSQL database name
        POSTGRES_USER: PostgreSQL user
        POSTGRES_PASSWORD: PostgreSQL password
        DATABASE_SCHEMA_PREFIX: Schema prefix (default: 'krai')
        
    Note: For Docker PostgreSQL, use type='postgresql' with POSTGRES_HOST=krai-postgres
    """
    
    # Determine database type from parameter or environment
    if database_type is None:
        database_type = os.getenv("DATABASE_TYPE", "postgresql").lower()
    else:
        database_type = database_type.lower()
    
    # Check for deprecated database type
    database_type = _check_deprecated_database_type(database_type)
    
    logger.info(f"Creating database adapter: {database_type}")
    
    # Create adapter based on type
    if database_type == "postgresql":
        return _create_postgresql_adapter(
            postgres_url=postgres_url,
            postgres_host=postgres_host,
            postgres_port=postgres_port,
            postgres_db=postgres_db,
            postgres_user=postgres_user,
            postgres_password=postgres_password,
            schema_prefix=schema_prefix
        )
    
    else:
        raise ValueError(
            f"Invalid database_type: {database_type}. "
            f"Must be one of: 'postgresql'"
        )




def _create_postgresql_adapter(
    postgres_url: Optional[str] = None,
    postgres_host: Optional[str] = None,
    postgres_port: Optional[int] = None,
    postgres_db: Optional[str] = None,
    postgres_user: Optional[str] = None,
    postgres_password: Optional[str] = None,
    schema_prefix: Optional[str] = None
) -> DatabaseAdapter:
    """Create a PostgreSQL adapter with configuration from parameters or environment."""
    from .postgresql_adapter import PostgreSQLAdapter
    
    # Get configuration from parameters or environment
    pg_url = postgres_url or os.getenv("DATABASE_CONNECTION_URL") or os.getenv("POSTGRES_URL")
    host = postgres_host or os.getenv("POSTGRES_HOST")
    port = postgres_port or int(os.getenv("POSTGRES_PORT", "5432"))
    database = postgres_db or os.getenv("POSTGRES_DB", "krai")
    user = postgres_user or os.getenv("POSTGRES_USER", "postgres")
    password = postgres_password or os.getenv("POSTGRES_PASSWORD")
    prefix = schema_prefix or os.getenv("DATABASE_SCHEMA_PREFIX", "krai")
    
    # If a full URL is provided, optionally normalize host when running outside Docker
    if pg_url:
        try:
            parsed = urlparse(pg_url)
            if parsed.hostname and not host:
                host = parsed.hostname

            # Simple Docker detection: /.dockerenv exists inside containers
            running_in_docker = os.path.exists("/.dockerenv") or os.getenv("KRAI_IN_DOCKER") == "1"

            if parsed.hostname in ("krai-postgres", "postgres") and not running_in_docker:
                userinfo = ""
                if parsed.username:
                    if parsed.password:
                        userinfo = f"{parsed.username}:{parsed.password}@"
                    else:
                        userinfo = f"{parsed.username}@"

                port_str = f":{parsed.port}" if parsed.port else ""
                netloc = f"{userinfo}127.0.0.1{port_str}"
                parsed = parsed._replace(netloc=netloc)
                original_pg_url = pg_url
                pg_url = urlunparse(parsed)
                host = "127.0.0.1"

                logger.info(
                    "Overriding PostgreSQL host for local execution: %r -> %r",
                    original_pg_url,
                    pg_url,
                )
        except Exception:
            # Best-effort normalization only; fall back silently on errors
            pass

    # Detect Docker environment and set defaults
    if not host:
        # Check if we're in a Docker environment
        if os.getenv("DATABASE_TYPE") == "postgresql":
            # Default to Docker service name for PostgreSQL
            host = "krai-postgres"
            logger.info("Detected potential Docker PostgreSQL environment, using host: krai-postgres")
        else:
            host = "localhost"
    
    # Special handling for Docker PostgreSQL defaults
    if host in ["krai-postgres", "postgres"]:
        logger.info("Detected Docker PostgreSQL environment")
        if not user:
            user = "krai_user"
        if not password:
            password = "krai_password"
    
    # Build connection URL if not provided
    if not pg_url:
        if not password:
            raise ValueError("POSTGRES_PASSWORD is required for PostgreSQL adapter")
        pg_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    logger.info(f"Creating PostgreSQL adapter: {host}:{port}/{database}")
    logger.info(f"Schema prefix: {prefix}")
    
    return PostgreSQLAdapter(
        postgres_url=pg_url,
        schema_prefix=prefix
    )


def _check_deprecated_database_type(database_type: str) -> str:
    """
    Check for deprecated database types and map them to current types.
    
    Args:
        database_type: The database type to check
        
    Returns:
        The updated database type
    """
    if database_type == 'docker_postgresql':
        logger.warning(
            "Database type 'docker_postgresql' is deprecated. "
            "Using 'postgresql' instead. Update your configuration to use 'postgresql'."
        )
        return 'postgresql'
    
    if database_type == 'supabase':
        logger.warning(
            "Database type 'supabase' is deprecated. "
            "Using 'postgresql' instead. Supabase support has been removed."
        )
        return 'postgresql'
    
    return database_type
