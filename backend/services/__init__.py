"""
KR-AI-Engine Services Module
Core services for database, storage, and AI operations
"""

from .database_service import DatabaseService
from .object_storage_service import ObjectStorageService
from backend.services.ai_service import AIService, create_ai_service
from backend.services.config_service import ConfigService
from backend.services.storage_factory import StorageFactory, create_storage_service
from backend.services.web_scraping_service import (
    WebScrapingService,
    create_web_scraping_service,
    FirecrawlBackend,
    BeautifulSoupBackend,
    WebScraperBackend,
)
from backend.services.link_enrichment_service import LinkEnrichmentService
from backend.services.structured_extraction_service import StructuredExtractionService
from backend.services.manufacturer_crawler import ManufacturerCrawler

__all__ = [
    "AIService",
    "ConfigService",
    "DatabaseService",
    "ObjectStorageService",
    "StorageFactory",
    "WebScrapingService",
    "create_ai_service",
    "create_storage_service",
    "create_web_scraping_service",
    "FirecrawlBackend",
    "BeautifulSoupBackend",
    "WebScraperBackend",
    "LinkEnrichmentService",
    "StructuredExtractionService",
    "ManufacturerCrawler",
]
