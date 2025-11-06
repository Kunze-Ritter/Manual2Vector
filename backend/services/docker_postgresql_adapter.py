"""
Docker PostgreSQL Database Adapter

Extends PostgreSQLAdapter with Docker-specific defaults and configuration.
Designed for local development with Docker Compose.
"""

import logging
from typing import Optional

from services.postgresql_adapter import PostgreSQLAdapter


class DockerPostgreSQLAdapter(PostgreSQLAdapter):
    """
    Docker PostgreSQL Database Adapter
    
    Extends PostgreSQLAdapter with Docker-specific defaults:
    - Default host: krai-postgres (Docker service name)
    - Default user: krai_user
    - Default password: krai_password
    - Default database: krai
    """
    
    def __init__(self, postgres_url: str, schema_prefix: str = "krai"):
        super().__init__(postgres_url, schema_prefix)
        self.logger = logging.getLogger("krai.database.docker_postgresql")
    
    async def connect(self) -> None:
        """Establish PostgreSQL connection pool with Docker-specific logging"""
        self.logger.info("Connecting to Docker PostgreSQL service...")
        await super().connect()
        self.logger.info("✅ Docker PostgreSQL adapter ready")
