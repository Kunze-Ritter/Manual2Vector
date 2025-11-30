#!/usr/bin/env python3
"""
Test Suite for Pipeline CLI

Comprehensive tests for the pipeline processor CLI including:
- Command parsing
- Stage execution
- Error handling
- Output formatting
"""

import asyncio
import pytest
import sys
from pathlib import Path
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch
from io import StringIO
import argparse

# Add backend to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import CLI module
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
import pipeline_processor
from backend.pipeline.master_pipeline import KRMasterPipeline
from backend.core.base_processor import Stage


class TestPipelineCLI:
    """Test suite for Pipeline CLI"""
    
    @pytest.fixture
    async def mock_pipeline(self):
        """Create a mock KRMasterPipeline"""
        pipeline = AsyncMock(spec=KRMasterPipeline)
        pipeline.initialize_services = AsyncMock()
        pipeline.get_available_stages = MagicMock(return_value=[
            'upload', 'text_extraction', 'table_extraction', 'svg_processing',
            'image_processing', 'visual_embedding', 'link_extraction',
            'chunk_preprocessing', 'classification', 'metadata_extraction',
            'parts_extraction', 'series_detection', 'storage',
            'embedding', 'search_indexing'
        ])
        pipeline.run_single_stage = AsyncMock(return_value={
            'success': True,
            'data': {'processed': 10},
            'stage': 'upload',
            'processor': 'upload'
        })
        pipeline.run_stages = AsyncMock(return_value={
            'document_id': 'test-doc-123',
            'total_stages': 3,
            'successful': 3,
            'failed': 0,
            'stage_results': [
                {'success': True, 'stage': 'upload'},
                {'success': True, 'stage': 'text_extraction'},
                {'success': True, 'stage': 'image_processing'}
            ],
            'success_rate': 100.0
        })
        pipeline.get_stage_status = AsyncMock(return_value={
            'document_id': 'test-doc-123',
            'stage_status': {
                'upload': {'status': 'completed'},
                'text_extraction': {'status': 'completed'},
                'image_processing': {'status': 'processing', 'metadata': {'progress': 50}}
            },
            'found': True
        })
        return pipeline
    
    def test_parse_stage_input_by_number(self):
        """Test parsing stage input by number"""
        stage = pipeline_processor.parse_stage_input("1")
        assert stage == Stage.UPLOAD
        
        stage = pipeline_processor.parse_stage_input("15")
        assert stage == Stage.SEARCH_INDEXING
    
    def test_parse_stage_input_by_name(self):
        """Test parsing stage input by name"""
        stage = pipeline_processor.parse_stage_input("upload")
        assert stage == Stage.UPLOAD
        
        stage = pipeline_processor.parse_stage_input("text_extraction")
        assert stage == Stage.TEXT_EXTRACTION
    
    def test_parse_stage_input_invalid(self):
        """Test parsing invalid stage input"""
        with pytest.raises(ValueError, match="Invalid stage number"):
            pipeline_processor.parse_stage_input("99")
        
        with pytest.raises(ValueError, match="Invalid stage"):
            pipeline_processor.parse_stage_input("invalid_stage")
    
    @pytest.mark.asyncio
    async def test_list_stages(self, mock_pipeline, capsys):
        """Test listing stages"""
        await pipeline_processor.list_stages(mock_pipeline)
        
        captured = capsys.readouterr()
        assert "Available Pipeline Stages:" in captured.out
        assert "upload" in captured.out
        assert "text_extraction" in captured.out
        assert "Total: 15 stages" in captured.out
    
    @pytest.mark.asyncio
    async def test_show_status(self, mock_pipeline, capsys):
        """Test showing document status"""
        document_id = "test-doc-123"
        await pipeline_processor.show_status(mock_pipeline, document_id)
        
        mock_pipeline.get_stage_status.assert_called_once_with(document_id)
        
        captured = capsys.readouterr()
        assert f"Document Status: {document_id}" in captured.out
        assert "✅ upload: completed" in captured.out
        assert "🔄 image_processing: processing" in captured.out
        assert "Progress: 50%" in captured.out
    
    @pytest.mark.asyncio
    async def test_show_status_not_found(self, mock_pipeline, capsys):
        """Test showing status for non-existent document"""
        mock_pipeline.get_stage_status.return_value = {
            'document_id': 'test-doc-123',
            'stage_status': {},
            'found': False,
            'error': 'Document not found'
        }
        
        await pipeline_processor.show_status(mock_pipeline, "test-doc-123")
        
        captured = capsys.readouterr()
        assert "❌ Document not found: test-doc-123" in captured.out
        assert "Error: Document not found" in captured.out
    
    @pytest.mark.asyncio
    async def test_run_single_stage(self, mock_pipeline, capsys):
        """Test running a single stage"""
        document_id = "test-doc-123"
        stage_input = "1"
        
        await pipeline_processor.run_single_stage(mock_pipeline, document_id, stage_input)
        
        mock_pipeline.run_single_stage.assert_called_once_with(document_id, Stage.UPLOAD)
        
        captured = capsys.readouterr()
        assert f"Running stage: upload for document: {document_id}" in captured.out
        assert "✅ Stage completed successfully!" in captured.out
        assert "processed: 10" in captured.out
    
    @pytest.mark.asyncio
    async def test_run_single_stage_failed(self, mock_pipeline, capsys):
        """Test running a single stage that fails"""
        mock_pipeline.run_single_stage.return_value = {
            'success': False,
            'error': 'Processing failed',
            'stage': 'upload'
        }
        
        await pipeline_processor.run_single_stage(mock_pipeline, "test-doc-123", "upload")
        
        captured = capsys.readouterr()
        assert "❌ Stage failed!" in captured.out
        assert "Error: Processing failed" in captured.out
    
    @pytest.mark.asyncio
    async def test_run_single_stage_invalid(self, mock_pipeline, capsys):
        """Test running an invalid stage"""
        await pipeline_processor.run_single_stage(mock_pipeline, "test-doc-123", "invalid")
        
        captured = capsys.readouterr()
        assert "❌ Error: Invalid stage" in captured.out
        assert "Use --list-stages to see available stages" in captured.out
    
    @pytest.mark.asyncio
    async def test_run_multiple_stages(self, mock_pipeline, capsys):
        """Test running multiple stages"""
        document_id = "test-doc-123"
        stage_inputs = ["1", "2", "5"]
        
        await pipeline_processor.run_multiple_stages(mock_pipeline, document_id, stage_inputs)
        
        mock_pipeline.run_stages.assert_called_once()
        args = mock_pipeline.run_stages.call_args[0]
        assert args[0] == document_id
        assert len(args[1]) == 3
        assert Stage.UPLOAD in args[1]
        assert Stage.TEXT_EXTRACTION in args[1]
        assert Stage.IMAGE_PROCESSING in args[1]
        
        captured = capsys.readouterr()
        assert f"Running 3 stages for document: {document_id}" in captured.out
        assert "Results Summary:" in captured.out
        assert "Total stages: 3" in captured.out
        assert "Successful: 3" in captured.out
        assert "Success rate: 100.0%" in captured.out
    
    @pytest.mark.asyncio
    async def test_run_smart_processing(self, mock_pipeline, capsys):
        """Test smart processing"""
        document_id = "test-doc-123"
        
        await pipeline_processor.run_smart_processing(mock_pipeline, document_id)
        
        mock_pipeline.get_stage_status.assert_called_once_with(document_id)
        mock_pipeline.run_stages.assert_called_once()
        
        captured = capsys.readouterr()
        assert f"Running smart processing for document: {document_id}" in captured.out
        assert "Smart Processing Results:" in captured.out
        assert "Stages attempted:" in captured.out
    
    @pytest.mark.asyncio
    async def test_run_smart_processing_no_stages(self, mock_pipeline, capsys):
        """Test smart processing when no stages need to run"""
        # Mock all stages as completed
        stage_status = {}
        for stage in Stage:
            stage_status[stage.value] = {'status': 'completed'}
        
        mock_pipeline.get_stage_status.return_value = {
            'document_id': 'test-doc-123',
            'stage_status': stage_status,
            'found': True
        }
        
        await pipeline_processor.run_smart_processing(mock_pipeline, "test-doc-123")
        
        captured = capsys.readouterr()
        assert "✅ All stages are already completed!" in captured.out
        # run_stages should not be called
        mock_pipeline.run_stages.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_run_smart_processing_document_not_found(self, mock_pipeline, capsys):
        """Test smart processing for non-existent document"""
        mock_pipeline.get_stage_status.return_value = {
            'document_id': 'test-doc-123',
            'stage_status': {},
            'found': False,
            'error': 'Document not found'
        }
        
        await pipeline_processor.run_smart_processing(mock_pipeline, "test-doc-123")
        
        captured = capsys.readouterr()
        assert "❌ Document not found: test-doc-123" in captured.out
        mock_pipeline.run_stages.assert_not_called()
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--list-stages'])
    @pytest.mark.asyncio
    async def test_main_list_stages(self, mock_pipeline_class):
        """Test main function with --list-stages"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline.get_available_stages = MagicMock(return_value=['upload', 'text_extraction'])
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            # Should exit normally (code 0)
            assert exc_info.value.code == 0
        
        output = mock_stdout.getvalue()
        assert "Available Pipeline Stages:" in output
        assert "upload" in output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123', '--stage', '1'])
    @pytest.mark.asyncio
    async def test_main_run_single_stage(self, mock_pipeline_class):
        """Test main function with --stage"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline.run_single_stage = AsyncMock(return_value={'success': True})
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 0
        
        mock_pipeline.run_single_stage.assert_called_once_with('test-doc-123', Stage.UPLOAD)
        output = mock_stdout.getvalue()
        assert "Running stage: upload" in output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123', '--status'])
    @pytest.mark.asyncio
    async def test_main_show_status(self, mock_pipeline_class):
        """Test main function with --status"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline.get_stage_status = AsyncMock(return_value={
            'document_id': 'test-doc-123',
            'stage_status': {'upload': {'status': 'completed'}},
            'found': True
        })
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 0
        
        mock_pipeline.get_stage_status.assert_called_once_with('test-doc-123')
        output = mock_stdout.getvalue()
        assert "Document Status: test-doc-123" in output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123', '--stages', '1,2,3'])
    @pytest.mark.asyncio
    async def test_main_run_multiple_stages(self, mock_pipeline_class):
        """Test main function with --stages"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline.run_stages = AsyncMock(return_value={
            'total_stages': 3, 'successful': 3, 'failed': 0, 'success_rate': 100.0
        })
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 0
        
        # Verify correct stages were passed
        args = mock_pipeline.run_stages.call_args[0]
        assert args[0] == 'test-doc-123'
        assert len(args[1]) == 3
        assert Stage.UPLOAD in args[1]
        assert Stage.TEXT_EXTRACTION in args[1]
        assert Stage.TABLE_EXTRACTION in args[1]
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123', '--all'])
    @pytest.mark.asyncio
    async def test_main_run_all_stages(self, mock_pipeline_class):
        """Test main function with --all"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline.run_stages = AsyncMock(return_value={
            'total_stages': 15, 'successful': 15, 'failed': 0, 'success_rate': 100.0
        })
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 0
        
        # Verify all stages were passed
        args = mock_pipeline.run_stages.call_args[0]
        assert args[0] == 'test-doc-123'
        assert len(args[1]) == 15  # All stages
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123', '--smart'])
    @pytest.mark.asyncio
    async def test_main_smart_processing(self, mock_pipeline_class):
        """Test main function with --smart"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline.get_stage_status = AsyncMock(return_value={
            'document_id': 'test-doc-123',
            'stage_status': {'upload': {'status': 'pending'}},
            'found': True
        })
        mock_pipeline.run_stages = AsyncMock(return_value={
            'total_stages': 1, 'successful': 1, 'failed': 0, 'success_rate': 100.0
        })
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 0
        
        mock_pipeline.get_stage_status.assert_called_once_with('test-doc-123')
        mock_pipeline.run_stages.assert_called_once()
        output = mock_stdout.getvalue()
        assert "Running smart processing" in output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--help'])
    @pytest.mark.asyncio
    async def test_main_help(self, mock_pipeline_class):
        """Test main function with --help"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            # argparse exits with code 0 for help
            assert exc_info.value.code == 0
        
        output = mock_stdout.getvalue()
        assert "KRAI Pipeline Processor CLI" in output
        assert "Examples:" in output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py'])
    @pytest.mark.asyncio
    async def test_main_no_args(self, mock_pipeline_class):
        """Test main function with no arguments (shows help)"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 0
        
        # Should show help when no arguments provided
        output = mock_stdout.getvalue()
        assert "KRAI Pipeline Processor CLI" in output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123'])
    @pytest.mark.asyncio
    async def test_main_missing_stage_arg(self, mock_pipeline_class):
        """Test main function when stage argument is missing"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            # Should exit with error code 1
            assert exc_info.value.code == 1
        
        error_output = mock_stderr.getvalue()
        assert "Error: --document-id is required" in error_output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123', '--stage', 'invalid'])
    @pytest.mark.asyncio
    async def test_main_invalid_stage(self, mock_pipeline_class):
        """Test main function with invalid stage"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 0
        
        output = mock_stdout.getvalue()
        assert "❌ Error: Invalid stage" in output
    
    @patch('pipeline_processor.KRMasterPipeline')
    @patch('sys.argv', ['pipeline_processor.py', '--document-id', 'test-doc-123', '--stage', '1', '--verbose'])
    @pytest.mark.asyncio
    async def test_main_verbose_mode(self, mock_pipeline_class):
        """Test main function with verbose mode"""
        mock_pipeline = AsyncMock()
        mock_pipeline.initialize_services = AsyncMock(side_effect=Exception("Test error"))
        mock_pipeline_class.return_value = mock_pipeline
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            with pytest.raises(SystemExit) as exc_info:
                await pipeline_processor.main()
            
            assert exc_info.value.code == 1
        
        error_output = mock_stderr.getvalue()
        assert "Unexpected error: Test error" in error_output
        # In verbose mode, should also show traceback
        assert "Traceback" in error_output


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
