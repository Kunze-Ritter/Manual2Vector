"""
KR-AI-Engine Services Module
Core services for storage, and AI operations
"""

from .object_storage_service import ObjectStorageService
from .ai_service import AIService, create_ai_service
from .config_service import ConfigService
from .storage_factory import StorageFactory, create_storage_service
from .web_scraping_service import (
    WebScrapingService,
    create_web_scraping_service,
    FirecrawlBackend,
    BeautifulSoupBackend,
    WebScraperBackend,
)
from .link_enrichment_service import LinkEnrichmentService
from .structured_extraction_service import StructuredExtractionService
from .manufacturer_crawler import ManufacturerCrawler
from .manufacturer_verification_service import ManufacturerVerificationService

__all__ = [
    "AIService",
    "ConfigService",
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
    "ManufacturerVerificationService",
]
