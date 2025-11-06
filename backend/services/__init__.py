"""
KR-AI-Engine Services Module
Core services for database, storage, and AI operations
"""

from .database_service import DatabaseService
from .object_storage_service import ObjectStorageService
from services.ai_service import AIService, create_ai_service
from services.config_service import ConfigService
from services.storage_factory import StorageFactory, create_storage_service
from services.web_scraping_service import (
    WebScrapingService,
    create_web_scraping_service,
    FirecrawlBackend,
    BeautifulSoupBackend,
    WebScraperBackend,
)
from services.link_enrichment_service import LinkEnrichmentService
from services.structured_extraction_service import StructuredExtractionService
from services.manufacturer_crawler import ManufacturerCrawler

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
