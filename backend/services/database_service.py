"""
Database Service (API) - Backward Compatibility Wrapper

This module provides backward compatibility for existing API code that uses DatabaseService.
It delegates all calls to the new adapter pattern via database_factory.

DEPRECATED: Use database_factory.create_database_adapter() for new code.
"""

import logging
from typing import Optional

from backend.services.database_factory import create_database_adapter
from backend.services.database_adapter import DatabaseAdapter


logger = logging.getLogger("krai.database.api_compat")


class DatabaseService:
    """
    Backward compatibility wrapper for DatabaseService (API version).
    
    Delegates all method calls to the adapter created by database_factory.
    This allows existing API code to continue working without modification.
    
    DEPRECATED: Use database_factory.create_database_adapter() for new code.
    """
    
    def __init__(self, supabase_url: str, supabase_key: str, postgres_url: Optional[str] = None):
        """
        Initialize DatabaseService (backward compatibility wrapper).
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon key
            postgres_url: PostgreSQL connection URL (optional, for cross-schema queries)
        """
        logger.info("DatabaseService (API) initialized - delegating to adapter factory")
        
        # Create underlying adapter using factory
        self._adapter: DatabaseAdapter = create_database_adapter(
            database_type="supabase",  # Default to Supabase for API compatibility
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            postgres_url=postgres_url
        )
        
        # Expose adapter attributes for backward compatibility
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.postgres_url = postgres_url
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
