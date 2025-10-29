"""
Database Adapter Factory

Factory pattern for creating database adapters based on configuration.
Supports multiple database backends: Supabase, PostgreSQL, Docker PostgreSQL.
"""

import os
import logging
from typing import Optional

from backend.services.database_adapter import DatabaseAdapter


logger = logging.getLogger("krai.database.factory")


def create_database_adapter(
    database_type: Optional[str] = None,
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    supabase_service_role_key: Optional[str] = None,
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
        database_type: Type of database adapter ('supabase', 'postgresql', 'docker_postgresql')
                      If None, reads from DATABASE_TYPE environment variable (default: 'supabase')
        supabase_url: Supabase project URL (for Supabase adapter)
        supabase_key: Supabase anon key (for Supabase adapter)
        supabase_service_role_key: Supabase service role key (for cross-schema queries)
        postgres_url: PostgreSQL connection URL (for PostgreSQL/Docker adapters)
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
        DATABASE_TYPE: Type of database adapter (default: 'supabase')
        SUPABASE_URL: Supabase project URL
        SUPABASE_ANON_KEY: Supabase anon key
        SUPABASE_SERVICE_ROLE_KEY: Supabase service role key
        DATABASE_CONNECTION_URL or POSTGRES_URL: PostgreSQL connection URL
        POSTGRES_HOST: PostgreSQL host
        POSTGRES_PORT: PostgreSQL port
        POSTGRES_DB: PostgreSQL database name
        POSTGRES_USER: PostgreSQL user
        POSTGRES_PASSWORD: PostgreSQL password
        DATABASE_SCHEMA_PREFIX: Schema prefix (default: 'krai')
    """
    
    # Determine database type from parameter or environment
    if database_type is None:
        database_type = os.getenv("DATABASE_TYPE", "supabase").lower()
    else:
        database_type = database_type.lower()
    
    logger.info(f"Creating database adapter: {database_type}")
    
    # Create adapter based on type
    if database_type == "supabase":
        return _create_supabase_adapter(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            supabase_service_role_key=supabase_service_role_key,
            postgres_url=postgres_url
        )
    
    elif database_type == "postgresql":
        return _create_postgresql_adapter(
            postgres_url=postgres_url,
            postgres_host=postgres_host,
            postgres_port=postgres_port,
            postgres_db=postgres_db,
            postgres_user=postgres_user,
            postgres_password=postgres_password,
            schema_prefix=schema_prefix
        )
    
    elif database_type == "docker_postgresql":
        return _create_docker_postgresql_adapter(
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
            f"Must be one of: 'supabase', 'postgresql', 'docker_postgresql'"
        )


def _create_supabase_adapter(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None,
    supabase_service_role_key: Optional[str] = None,
    postgres_url: Optional[str] = None
) -> DatabaseAdapter:
    """Create a Supabase adapter with configuration from parameters or environment."""
    from backend.services.supabase_adapter import SupabaseAdapter
    
    # Get configuration from parameters or environment
    url = supabase_url or os.getenv("SUPABASE_URL")
    key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
    service_role_key = supabase_service_role_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    pg_url = postgres_url or os.getenv("DATABASE_CONNECTION_URL") or os.getenv("POSTGRES_URL")
    
    # Validate required configuration
    if not url:
        raise ValueError("SUPABASE_URL is required for Supabase adapter")
    if not key:
        raise ValueError("SUPABASE_ANON_KEY is required for Supabase adapter")
    
    logger.info(f"Creating Supabase adapter: {url}")
    logger.info(f"Service role key: {'✅ Available' if service_role_key else '❌ Not available'}")
    logger.info(f"Direct PostgreSQL: {'✅ Available' if pg_url else '❌ Not available'}")
    
    return SupabaseAdapter(
        supabase_url=url,
        supabase_key=key,
        postgres_url=pg_url,
        service_role_key=service_role_key
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
    from backend.services.postgresql_adapter import PostgreSQLAdapter
    
    # Get configuration from parameters or environment
    pg_url = postgres_url or os.getenv("DATABASE_CONNECTION_URL") or os.getenv("POSTGRES_URL")
    host = postgres_host or os.getenv("POSTGRES_HOST", "localhost")
    port = postgres_port or int(os.getenv("POSTGRES_PORT", "5432"))
    database = postgres_db or os.getenv("POSTGRES_DB", "krai")
    user = postgres_user or os.getenv("POSTGRES_USER", "postgres")
    password = postgres_password or os.getenv("POSTGRES_PASSWORD")
    prefix = schema_prefix or os.getenv("DATABASE_SCHEMA_PREFIX", "krai")
    
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


def _create_docker_postgresql_adapter(
    postgres_url: Optional[str] = None,
    postgres_host: Optional[str] = None,
    postgres_port: Optional[int] = None,
    postgres_db: Optional[str] = None,
    postgres_user: Optional[str] = None,
    postgres_password: Optional[str] = None,
    schema_prefix: Optional[str] = None
) -> DatabaseAdapter:
    """Create a Docker PostgreSQL adapter with Docker-specific defaults."""
    from backend.services.docker_postgresql_adapter import DockerPostgreSQLAdapter
    
    # Get configuration from parameters or environment (Docker defaults)
    pg_url = postgres_url or os.getenv("DATABASE_CONNECTION_URL") or os.getenv("POSTGRES_URL")
    host = postgres_host or os.getenv("POSTGRES_HOST", "krai-postgres")  # Docker service name
    port = postgres_port or int(os.getenv("POSTGRES_PORT", "5432"))
    database = postgres_db or os.getenv("POSTGRES_DB", "krai")
    user = postgres_user or os.getenv("POSTGRES_USER", "krai_user")
    password = postgres_password or os.getenv("POSTGRES_PASSWORD", "krai_password")
    prefix = schema_prefix or os.getenv("DATABASE_SCHEMA_PREFIX", "krai")
    
    # Build connection URL if not provided
    if not pg_url:
        pg_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    logger.info(f"Creating Docker PostgreSQL adapter: {host}:{port}/{database}")
    logger.info(f"Schema prefix: {prefix}")
    
    return DockerPostgreSQLAdapter(
        postgres_url=pg_url,
        schema_prefix=prefix
    )
