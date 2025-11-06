"""
Unit tests for LLM provider switching behavior.

Tests dynamic switching between different LLM providers (Ollama, OpenAI, etc.)
through StructuredExtractionService and WebScrapingService using environment
configuration and provider validation.
"""

import pytest
import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, patch
import json

pytest.mark.unit = pytest.mark.unit


class TestLLMProviderSwitching:
    """Test LLM provider switching functionality through services."""

    @pytest.fixture
    def mock_config_service(self):
        """Mock ConfigService with different provider configurations."""
        config = MagicMock()
        
        def get_scraping_config():
            return {
                'backend': 'firecrawl',
                'firecrawl_api_url': 'http://localhost:3002',
                'firecrawl_llm_provider': os.getenv('FIRECRAWL_LLM_PROVIDER', 'ollama'),
                'firecrawl_model_name': os.getenv('FIRECRAWL_MODEL_NAME', 'llama3.2:latest'),
                'firecrawl_embedding_model': os.getenv('FIRECRAWL_EMBEDDING_MODEL', 'nomic-embed-text:latest'),
                'extraction_timeout': 60,
                'extraction_confidence_threshold': 0.5,
            }
        
        config.get_scraping_config = get_scraping_config
        return config

    @pytest.fixture
    def mock_database_service(self):
        """Mock database service."""
        service = MagicMock()
        service.client = MagicMock()
        service.service_client = MagicMock()
        return service

    @pytest.fixture
    def mock_web_scraping_service(self):
        """Mock WebScrapingService."""
        service = MagicMock()
        
        def scrape_url(url, **kwargs):
            return {
                'success': True,
                'backend': 'firecrawl',
                'content': '# Test Content\n\nProduct model: C750i',
                'html': '<html><body>Test</body></html>',
                'metadata': {'status_code': 200}
            }
        
        service.scrape_url = AsyncMock(side_effect=scrape_url)
        
        def extract_structured_data(url, schema, **kwargs):
            provider = os.getenv('FIRECRAWL_LLM_PROVIDER', 'ollama')
            model = os.getenv('FIRECRAWL_MODEL_NAME', 'llama3.2:latest')
            
            return {
                'success': True,
                'backend': 'firecrawl',
                'data': {'model_number': 'C750i', 'manufacturer': 'Konica Minolta'},
                'confidence': 0.85,
                'llm_provider': provider,
                'llm_model': model
            }
        
        service.extract_structured_data = AsyncMock(side_effect=extract_structured_data)
        return service

    @pytest.mark.asyncio
    async def test_ollama_provider_via_structured_extraction(self, mock_database_service, mock_web_scraping_service):
        """Test Ollama provider selection through StructuredExtractionService."""
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'ollama',
            'FIRECRAWL_MODEL_NAME': 'llama3.2:latest'
        }):
            from backend.services.structured_extraction_service import StructuredExtractionService
            
            service = StructuredExtractionService(
                database_service=mock_database_service,
                web_scraping_service=mock_web_scraping_service
            )
            
            # Test extraction with Ollama provider
            result = await service.extract_product_specs(
                url='http://example.com/product',
                manufacturer_id='test-mfr'
            )
            
            # Verify provider and model are persisted
            assert result['success'] is True
            assert result['llm_provider'] == 'ollama'
            assert result['llm_model'] == 'llama3.2:latest'
            
            # Verify database call includes provider info
            mock_database_service.client.table.assert_called()
            call_args = mock_database_service.client.table.return_value.insert.call_args[0][0]
            assert call_args['llm_provider'] == 'ollama'
            assert call_args['llm_model'] == 'llama3.2:latest'

    @pytest.mark.asyncio
    async def test_openai_provider_via_structured_extraction(self, mock_database_service, mock_web_scraping_service):
        """Test OpenAI provider selection through StructuredExtractionService."""
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'openai',
            'FIRECRAWL_MODEL_NAME': 'gpt-3.5-turbo'
        }):
            from backend.services.structured_extraction_service import StructuredExtractionService
            
            service = StructuredExtractionService(
                database_service=mock_database_service,
                web_scraping_service=mock_web_scraping_service
            )
            
            # Test extraction with OpenAI provider
            result = await service.extract_error_codes(
                url='http://example.com/error-codes',
                document_id='test-doc'
            )
            
            # Verify provider and model are persisted
            assert result['success'] is True
            assert result['llm_provider'] == 'openai'
            assert result['llm_model'] == 'gpt-3.5-turbo'

    @pytest.mark.asyncio
    async def test_provider_switching_runtime_change(self, mock_database_service, mock_web_scraping_service):
        """Test provider switching at runtime through environment changes."""
        from backend.services.structured_extraction_service import StructuredExtractionService
        
        # Start with Ollama
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'ollama',
            'FIRECRAWL_MODEL_NAME': 'llama3.2:latest'
        }):
            service = StructuredExtractionService(
                database_service=mock_database_service,
                web_scraping_service=mock_web_scraping_service
            )
            
            result1 = await service.extract_product_specs(
                url='http://example.com/product',
                manufacturer_id='test-mfr'
            )
            
            assert result1['llm_provider'] == 'ollama'
        
        # Switch to OpenAI
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'openai',
            'FIRECRAWL_MODEL_NAME': 'gpt-4'
        }, clear=False):
            # Service should pick up new environment values
            result2 = await service.extract_service_manual(
                url='http://example.com/manual',
                product_id='test-product'
            )
            
            assert result2['llm_provider'] == 'openai'
            assert result2['llm_model'] == 'gpt-4'

    @pytest.mark.asyncio
    async def test_web_scraping_service_provider_inheritance(self, mock_config_service):
        """Test WebScrapingService inherits provider configuration correctly."""
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'anthropic',
            'FIRECRAWL_MODEL_NAME': 'claude-3-sonnet'
        }):
            from backend.services.web_scraping_service import create_web_scraping_service
            
            service = create_web_scraping_service(backend='firecrawl', config_service=mock_config_service)
            
            # Test structured extraction includes provider info
            result = await service.extract_structured_data(
                url='http://example.com/product',
                schema={'type': 'object', 'properties': {'model': {'type': 'string'}}}
            )
            
            assert result['success'] is True
            assert result['llm_provider'] == 'anthropic'
            assert result['llm_model'] == 'claude-3-sonnet'

    @pytest.mark.asyncio
    async def test_provider_configuration_defaults(self, mock_database_service, mock_web_scraping_service):
        """Test provider configuration falls back to defaults when env vars are missing."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            from backend.services.structured_extraction_service import StructuredExtractionService
            
            service = StructuredExtractionService(
                database_service=mock_database_service,
                web_scraping_service=mock_web_scraping_service
            )
            
            result = await service.extract_parts_list(
                url='http://example.com/parts',
                product_id='test-product'
            )
            
            # Should fall back to defaults
            assert result['success'] is True
            assert result['llm_provider'] == 'ollama'  # Default
            assert result['llm_model'] == 'llama3.2:latest'  # Default

    @pytest.mark.asyncio
    async def test_provider_persistence_across_extraction_types(self, mock_database_service, mock_web_scraping_service):
        """Test provider consistency across different extraction types."""
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'openai',
            'FIRECRAWL_MODEL_NAME': 'gpt-4'
        }):
            from backend.services.structured_extraction_service import StructuredExtractionService
            
            service = StructuredExtractionService(
                database_service=mock_database_service,
                web_scraping_service=mock_web_scraping_service
            )
            
            # Test multiple extraction types
            product_result = await service.extract_product_specs(
                url='http://example.com/product',
                manufacturer_id='test-mfr'
            )
            
            error_result = await service.extract_error_codes(
                url='http://example.com/errors',
                document_id='test-doc'
            )
            
            manual_result = await service.extract_service_manual(
                url='http://example.com/manual',
                product_id='test-product'
            )
            
            parts_result = await service.extract_parts_list(
                url='http://example.com/parts',
                product_id='test-product'
            )
            
            # All should use the same provider
            for result in [product_result, error_result, manual_result, parts_result]:
                assert result['llm_provider'] == 'openai'
                assert result['llm_model'] == 'gpt-4'

    @pytest.mark.asyncio
    async def test_invalid_provider_handling(self, mock_database_service, mock_web_scraping_service):
        """Test handling of invalid provider configuration."""
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'invalid_provider',
            'FIRECRAWL_MODEL_NAME': 'invalid_model'
        }):
            from backend.services.structured_extraction_service import StructuredExtractionService
            
            service = StructuredExtractionService(
                database_service=mock_database_service,
                web_scraping_service=mock_web_scraping_service
            )
            
            # Service should still attempt extraction with configured provider
            # The actual validation happens at the Firecrawl level
            result = await service.extract_product_specs(
                url='http://example.com/product',
                manufacturer_id='test-mfr'
            )
            
            # Provider info should still be persisted even if invalid
            assert result['llm_provider'] == 'invalid_provider'
            assert result['llm_model'] == 'invalid_model'

    def test_config_service_provider_integration(self, mock_config_service):
        """Test ConfigService integration for provider configuration."""
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'openai',
            'FIRECRAWL_MODEL_NAME': 'gpt-3.5-turbo'
        }):
            config = mock_config_service.get_scraping_config()
            
            assert config['firecrawl_llm_provider'] == 'openai'
            assert config['firecrawl_model_name'] == 'gpt-3.5-turbo'
            assert 'firecrawl_embedding_model' in config

    @pytest.mark.asyncio
    async def test_provider_environment_override(self, mock_config_service):
        """Test environment variables override config service values."""
        # Config service returns one value, environment overrides
        mock_config_service.get_scraping_config.return_value = {
            'firecrawl_llm_provider': 'ollama',  # This should be overridden
            'firecrawl_model_name': 'llama3.2:latest',
        }
        
        with patch.dict(os.environ, {
            'FIRECRAWL_LLM_PROVIDER': 'openai',  # Override
            'FIRECRAWL_MODEL_NAME': 'gpt-4'  # Override
        }):
            from backend.services.web_scraping_service import create_web_scraping_service
            
            service = create_web_scraping_service(backend='firecrawl', config_service=mock_config_service)
            
            result = await service.extract_structured_data(
                url='http://example.com/test',
                schema={'type': 'object'}
            )
            
            # Should use environment override, not config service
            assert result['llm_provider'] == 'openai'
            assert result['llm_model'] == 'gpt-4'
