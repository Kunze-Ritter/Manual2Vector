"""
Database Service (API) - Backward Compatibility Wrapper

This module provides backward compatibility for existing API code that uses DatabaseService.
It delegates all calls to the new adapter pattern via database_factory.
Supports both Supabase and generic PostgreSQL connections.

DEPRECATED: Use database_factory.create_database_adapter() for new code.
"""

import logging
import os
from typing import Optional

from services.database_factory import create_database_adapter
from services.database_adapter import DatabaseAdapter


logger = logging.getLogger("krai.database.api_compat")


class DatabaseService:
    """
    Backward compatibility wrapper for DatabaseService (API version).
    
    Delegates all method calls to the adapter created by database_factory.
    This allows existing API code to continue working without modification.
    
    DEPRECATED: Use database_factory.create_database_adapter() for new code.
    """
    
    def __init__(self, 
                 supabase_url: Optional[str] = None,
                 supabase_key: Optional[str] = None,
                 postgres_url: Optional[str] = None,
                 database_type: Optional[str] = None,
                 postgres_host: Optional[str] = None,
                 postgres_port: Optional[int] = None,
                 postgres_db: Optional[str] = None,
                 postgres_user: Optional[str] = None,
                 postgres_password: Optional[str] = None):
        """
        Initialize DatabaseService (backward compatibility wrapper).
        
        Args:
            supabase_url: Supabase project URL (for backward compatibility)
            supabase_key: Supabase anon key (for backward compatibility)
            postgres_url: PostgreSQL connection URL (optional)
            database_type: Type of database adapter ('supabase', 'postgresql')
            postgres_host: PostgreSQL host (alternative to postgres_url)
            postgres_port: PostgreSQL port (alternative to postgres_url)
            postgres_db: PostgreSQL database name (alternative to postgres_url)
            postgres_user: PostgreSQL user (alternative to postgres_url)
            postgres_password: PostgreSQL password (alternative to postgres_url)
            
        Note: Automatically selects adapter based on provided parameters.
        """
        logger.info("DatabaseService (API) initialized - delegating to adapter factory")
        
        # Determine database type
        if supabase_url:
            db_type = 'supabase'
            if not database_type:
                logger.warning("Direct Supabase parameters are deprecated. Use database_type='supabase' with environment variables.")
        else:
            db_type = database_type or os.getenv('DATABASE_TYPE', 'postgresql')
        
        # Create underlying adapter using factory
        self._adapter: DatabaseAdapter = create_database_adapter(
            database_type=db_type,
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            postgres_url=postgres_url,
            postgres_host=postgres_host,
            postgres_port=postgres_port,
            postgres_db=postgres_db,
            postgres_user=postgres_user,
            postgres_password=postgres_password
        )
        
        # Expose adapter attributes for backward compatibility
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.postgres_url = postgres_url
        self.database_type = db_type
        self.logger = self._adapter.logger
    
    def __getattr__(self, name: str):
        """
        Delegate all attribute/method access to the underlying adapter.
        
        This provides transparent backward compatibility - any method call
        on DatabaseService is automatically forwarded to the adapter.
        """
        return getattr(self._adapter, name)
    
    @property
    def client(self):
        """Access to Supabase client (backward compatibility)"""
        if hasattr(self._adapter, 'client'):
            return self._adapter.client
        return None
    
    @property
    def pg_pool(self):
        """Access to PostgreSQL connection pool (backward compatibility)"""
        if hasattr(self._adapter, 'pg_pool'):
            return self._adapter.pg_pool
        return None
