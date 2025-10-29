"""
Database Service (Production) - Backward Compatibility Wrapper

This module provides backward compatibility for existing code that uses DatabaseService.
It delegates all calls to the new SupabaseAdapter via __getattr__.

DEPRECATED: Use database_factory.create_database_adapter() for new code.
"""

import logging
from typing import Optional

from backend.services.supabase_adapter import SupabaseAdapter


logger = logging.getLogger("krai.database.compat")


class DatabaseService:
    """
    Backward compatibility wrapper for DatabaseService.
    
    Delegates all method calls to SupabaseAdapter.
    This allows existing code to continue working without modification.
    
    DEPRECATED: Use database_factory.create_database_adapter() for new code.
    """
    
    def __init__(self, supabase_url: str, supabase_key: str, postgres_url: Optional[str] = None, service_role_key: Optional[str] = None):
        """
        Initialize DatabaseService (backward compatibility wrapper).
        
        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase anon key
            postgres_url: PostgreSQL connection URL (optional, for cross-schema queries)
            service_role_key: Supabase service role key (optional, for elevated permissions)
        """
        logger.info("DatabaseService (production) initialized - delegating to SupabaseAdapter")
        
        # Create underlying adapter
        self._adapter = SupabaseAdapter(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            postgres_url=postgres_url,
            service_role_key=service_role_key
        )
        
        # Expose adapter attributes for backward compatibility
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.postgres_url = postgres_url
        self.service_role_key = service_role_key
        self.logger = self._adapter.logger
    
    def __getattr__(self, name: str):
        """
        Delegate all attribute/method access to the underlying adapter.
        
        This provides transparent backward compatibility - any method call
        on DatabaseService is automatically forwarded to SupabaseAdapter.
        """
        return getattr(self._adapter, name)
    
    @property
    def client(self):
        """Access to Supabase client (backward compatibility)"""
        return self._adapter.client
    
    @property
    def service_client(self):
        """Access to Supabase service role client (backward compatibility)"""
        return self._adapter.service_client
    
    @property
    def pg_pool(self):
        """Access to PostgreSQL connection pool (backward compatibility)"""
        return self._adapter.pg_pool
