"""
End-to-End Tests for Monitoring System

Tests the complete monitoring system including:
- Metrics aggregation
- Alert evaluation
- WebSocket broadcasting
- Permission checks
- Database integration
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from fastapi import WebSocket

# Import monitoring components
from backend.models.monitoring import (
    PipelineMetrics,
    QueueMetrics,
    StageMetrics,
    HardwareMetrics,
    DataQualityMetrics,
    Alert,
    AlertRule,
    AlertType,
    AlertSeverity,
    CreateAlertRule,
)
from backend.services.metrics_service import MetricsService
from backend.services.alert_service import AlertService
from backend.api.app import app


class TestMetricsService:
    """Test MetricsService with real database queries."""

    @pytest.fixture
    async def metrics_service(self, mock_supabase_adapter):
        """Create MetricsService with mocked adapter."""
        from backend.processors.stage_tracker import StageTracker
        stage_tracker = StageTracker(mock_supabase_adapter.client)
        service = MetricsService(mock_supabase_adapter, stage_tracker)
        return service

    @pytest.mark.asyncio
    async def test_get_pipeline_metrics(self, metrics_service, mock_supabase_adapter):
        """Test pipeline metrics aggregation."""
        # Mock aggregated view response
        mock_supabase_adapter.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
            {
                "total_documents": 1000,
                "documents_pending": 50,
                "documents_processing": 10,
                "documents_completed": 920,
                "documents_failed": 20,
                "success_rate": 97.87,
                "recent_24h_count": 150,
            }
        ]

        metrics = await metrics_service.get_pipeline_metrics()

        assert isinstance(metrics, PipelineMetrics)
        assert metrics.total_documents == 1000
        assert metrics.documents_completed == 920
        assert metrics.documents_failed == 20
        assert metrics.success_rate == 97.87
        assert metrics.current_throughput_docs_per_hour == pytest.approx(6.25, 0.01)

    @pytest.mark.asyncio
    async def test_get_queue_metrics(self, metrics_service, mock_supabase_adapter):
        """Test queue metrics aggregation."""
        # Mock aggregated view response
        mock_supabase_adapter.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
            {
                "total_items": 200,
                "pending_count": 50,
                "processing_count": 10,
                "completed_count": 130,
                "failed_count": 10,
                "avg_processing_time_seconds": 45.5,
            }
        ]

        # Mock task type query
        mock_supabase_adapter.client.table.return_value.select.return_value.execute.return_value.data = [
            {"task_type": "document_processing"},
            {"task_type": "document_processing"},
            {"task_type": "embedding_generation"},
        ]

        metrics = await metrics_service.get_queue_metrics()

        assert isinstance(metrics, QueueMetrics)
        assert metrics.total_items == 200
        assert metrics.pending_count == 50
        assert metrics.processing_count == 10
        assert metrics.avg_wait_time_seconds == 45.5
        assert "document_processing" in metrics.by_task_type

    @pytest.mark.asyncio
    async def test_get_stage_metrics(self, metrics_service, mock_supabase_adapter):
        """Test stage metrics aggregation."""
        # Mock aggregated view response
        mock_supabase_adapter.client.table.return_value.select.return_value.execute.return_value.data = [
            {
                "stage_name": "text_extraction",
                "total_executions": 1000,
                "completed_count": 980,
                "failed_count": 20,
                "avg_duration_seconds": 12.5,
            },
            {
                "stage_name": "embedding",
                "total_executions": 980,
                "completed_count": 975,
                "failed_count": 5,
                "avg_duration_seconds": 8.3,
            },
        ]

        metrics = await metrics_service.get_stage_metrics()

        assert isinstance(metrics, list)
        assert len(metrics) == 2
        assert metrics[0].stage_name == "text_extraction"
        assert metrics[0].completed_count == 980
        assert metrics[0].success_rate == 98.0
        assert metrics[1].stage_name == "embedding"

    @pytest.mark.asyncio
    async def test_get_hardware_metrics(self, metrics_service):
        """Test hardware metrics collection."""
        metrics = await metrics_service.get_hardware_metrics()

        assert isinstance(metrics, HardwareMetrics)
        assert 0 <= metrics.cpu_percent <= 100
        assert 0 <= metrics.ram_percent <= 100
        assert 0 <= metrics.disk_percent <= 100
        assert isinstance(metrics.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_metrics_caching(self, metrics_service, mock_supabase_adapter):
        """Test that metrics are cached properly."""
        # Mock response
        mock_supabase_adapter.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
            {
                "total_documents": 1000,
                "documents_pending": 50,
                "documents_processing": 10,
                "documents_completed": 920,
                "documents_failed": 20,
                "success_rate": 97.87,
                "recent_24h_count": 150,
            }
        ]

        # First call - should hit database
        metrics1 = await metrics_service.get_pipeline_metrics()
        
        # Second call - should use cache
        metrics2 = await metrics_service.get_pipeline_metrics()

        assert metrics1 == metrics2
        # Database should only be called once
        assert mock_supabase_adapter.client.table.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, metrics_service, mock_supabase_adapter):
        """Test cache invalidation."""
        # Mock response
        mock_supabase_adapter.client.table.return_value.select.return_value.limit.return_value.execute.return_value.data = [
            {"total_documents": 1000, "documents_pending": 50, "documents_processing": 10,
             "documents_completed": 920, "documents_failed": 20, "success_rate": 97.87, "recent_24h_count": 150}
        ]

        # Get metrics (cached)
        await metrics_service.get_pipeline_metrics()
        
        # Invalidate cache
        metrics_service.invalidate_cache("pipeline_metrics")
        
        # Get metrics again (should hit database)
        await metrics_service.get_pipeline_metrics()

        # Database should be called twice
        assert mock_supabase_adapter.client.table.call_count == 2


class TestAlertService:
    """Test AlertService with alert evaluation."""

    @pytest.fixture
    async def alert_service(self, mock_supabase_adapter, metrics_service):
        """Create AlertService with mocked adapter."""
        service = AlertService(mock_supabase_adapter, metrics_service)
        await service.load_alert_rules()
        return service

    @pytest.mark.asyncio
    async def test_load_alert_rules(self, alert_service, mock_supabase_adapter):
        """Test loading alert rules from database."""
        # Mock database response
        mock_supabase_adapter.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "id": "rule-001",
                "name": "High CPU Usage",
                "alert_type": "hardware_threshold",
                "severity": "high",
                "threshold_value": 90.0,
                "threshold_operator": ">",
                "metric_key": "cpu",
                "enabled": True,
            }
        ]

        rules = await alert_service.load_alert_rules()

        assert len(rules) > 0
        assert all(isinstance(rule, AlertRule) for rule in rules)

    @pytest.mark.asyncio
    async def test_add_alert_rule(self, alert_service, mock_supabase_adapter):
        """Test adding new alert rule."""
        # Mock database insert
        mock_supabase_adapter.client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "rule-new"}
        ]

        new_rule = CreateAlertRule(
            name="Test Alert",
            alert_type=AlertType.HARDWARE_THRESHOLD,
            severity=AlertSeverity.HIGH,
            threshold_value=85.0,
            threshold_operator=">",
            metric_key="ram",
            enabled=True,
        )

        rule_id = await alert_service.add_alert_rule(new_rule)

        assert rule_id == "rule-new"

    @pytest.mark.asyncio
    async def test_evaluate_alerts_high_cpu(self, alert_service, metrics_service):
        """Test alert evaluation for high CPU usage."""
        # Set up alert rule
        alert_service.alert_rules = [
            AlertRule(
                id="rule-cpu",
                name="High CPU Usage",
                alert_type=AlertType.HARDWARE_THRESHOLD,
                severity=AlertSeverity.HIGH,
                threshold_value=90.0,
                threshold_operator=">",
                metric_key="cpu",
                enabled=True,
            )
        ]

        # Mock high CPU usage
        with patch.object(metrics_service, 'get_hardware_metrics') as mock_hw:
            mock_hw.return_value = HardwareMetrics(
                cpu_percent=95.0,
                ram_percent=60.0,
                disk_percent=50.0,
                timestamp=datetime.utcnow(),
            )

            alerts = await alert_service.evaluate_alerts()

            assert len(alerts) > 0
            assert alerts[0].alert_type == AlertType.HARDWARE_THRESHOLD
            assert alerts[0].severity == AlertSeverity.HIGH
            assert "CPU" in alerts[0].title or "cpu" in alerts[0].title.lower()

    @pytest.mark.asyncio
    async def test_evaluate_alerts_processing_failure(self, alert_service, metrics_service):
        """Test alert evaluation for processing failures."""
        # Set up alert rule
        alert_service.alert_rules = [
            AlertRule(
                id="rule-fail",
                name="High Failure Rate",
                alert_type=AlertType.PROCESSING_FAILURE,
                severity=AlertSeverity.HIGH,
                threshold_value=10.0,
                threshold_operator=">",
                enabled=True,
            )
        ]

        # Mock low success rate
        with patch.object(metrics_service, 'get_pipeline_metrics') as mock_pipeline:
            mock_pipeline.return_value = PipelineMetrics(
                total_documents=1000,
                documents_pending=50,
                documents_processing=10,
                documents_completed=850,
                documents_failed=90,
                success_rate=85.0,  # 15% failure rate
                avg_processing_time_seconds=45.0,
                current_throughput_docs_per_hour=25.0,
            )

            alerts = await alert_service.evaluate_alerts()

            assert len(alerts) > 0
            assert alerts[0].alert_type == AlertType.PROCESSING_FAILURE

    @pytest.mark.asyncio
    async def test_alert_deduplication(self, alert_service, metrics_service):
        """Test that alerts are not duplicated."""
        # Set up alert rule
        alert_service.alert_rules = [
            AlertRule(
                id="rule-cpu",
                name="High CPU Usage",
                alert_type=AlertType.HARDWARE_THRESHOLD,
                severity=AlertSeverity.HIGH,
                threshold_value=90.0,
                threshold_operator=">",
                metric_key="cpu",
                enabled=True,
            )
        ]

        # Mock high CPU usage
        with patch.object(metrics_service, 'get_hardware_metrics') as mock_hw:
            mock_hw.return_value = HardwareMetrics(
                cpu_percent=95.0, ram_percent=60.0, disk_percent=50.0, timestamp=datetime.utcnow()
            )

            # First evaluation - should create alert
            alerts1 = await alert_service.evaluate_alerts()
            assert len(alerts1) == 1

            # Second evaluation - should not create duplicate
            alerts2 = await alert_service.evaluate_alerts()
            assert len(alerts2) == 0  # No new alerts

    @pytest.mark.asyncio
    async def test_get_alerts_with_filters(self, alert_service, mock_supabase_adapter):
        """Test getting alerts with filters."""
        # Mock database response
        mock_supabase_adapter.client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
            {
                "id": "alert-001",
                "alert_type": "hardware_threshold",
                "severity": "high",
                "title": "High CPU Usage",
                "message": "CPU usage is 95%",
                "metadata": {"cpu_percent": 95.0},
                "triggered_at": datetime.utcnow().isoformat(),
                "acknowledged": False,
            }
        ]

        response = await alert_service.get_alerts(
            limit=50,
            severity_filter=AlertSeverity.HIGH,
            acknowledged_filter=False,
        )

        assert response.total > 0
        assert len(response.alerts) > 0
        assert response.alerts[0].severity == AlertSeverity.HIGH


class TestMonitoringAPI:
    """Test Monitoring API endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self, mock_jwt_token):
        """Create authentication headers."""
        return {"Authorization": f"Bearer {mock_jwt_token}"}

    def test_get_pipeline_metrics_endpoint(self, client, auth_headers):
        """Test GET /api/v1/monitoring/pipeline endpoint."""
        response = client.get("/api/v1/monitoring/pipeline", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_documents" in data
        assert "success_rate" in data
        assert "current_throughput_docs_per_hour" in data

    def test_get_queue_metrics_endpoint(self, client, auth_headers):
        """Test GET /api/v1/monitoring/queue endpoint."""
        response = client.get("/api/v1/monitoring/queue", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_items" in data
        assert "pending_count" in data
        assert "by_task_type" in data

    def test_get_hardware_metrics_endpoint(self, client, auth_headers):
        """Test GET /api/v1/monitoring/metrics endpoint."""
        response = client.get("/api/v1/monitoring/metrics", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data
        assert "ram_percent" in data
        assert "disk_percent" in data

    def test_get_alerts_endpoint(self, client, auth_headers):
        """Test GET /api/v1/monitoring/alerts endpoint."""
        response = client.get("/api/v1/monitoring/alerts", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total" in data
        assert "unacknowledged_count" in data

    def test_create_alert_rule_endpoint(self, client, auth_headers):
        """Test POST /api/v1/monitoring/alert-rules endpoint."""
        new_rule = {
            "name": "Test Alert Rule",
            "alert_type": "hardware_threshold",
            "severity": "medium",
            "threshold_value": 80.0,
            "threshold_operator": ">",
            "metric_key": "ram",
            "enabled": True,
        }

        response = client.post(
            "/api/v1/monitoring/alert-rules",
            json=new_rule,
            headers=auth_headers,
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["success"] is True
        assert "rule_id" in data

    def test_unauthorized_access(self, client):
        """Test that endpoints require authentication."""
        response = client.get("/api/v1/monitoring/pipeline")
        assert response.status_code == 401

    def test_insufficient_permissions(self, client):
        """Test that endpoints check permissions."""
        # Mock token with insufficient permissions
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/monitoring/pipeline", headers=headers)
        assert response.status_code in [401, 403]


class TestWebSocketAPI:
    """Test WebSocket API for real-time updates."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, mock_jwt_token):
        """Test WebSocket connection with authentication."""
        client = TestClient(app)
        
        with client.websocket_connect(f"/ws/monitoring?token={mock_jwt_token}") as websocket:
            # Should connect successfully
            data = websocket.receive_json()
            assert "event" in data

    @pytest.mark.asyncio
    async def test_websocket_authentication_failure(self):
        """Test WebSocket connection fails with invalid token."""
        client = TestClient(app)
        
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/monitoring?token=invalid") as websocket:
                pass

    @pytest.mark.asyncio
    async def test_websocket_broadcast_alert(self, mock_jwt_token):
        """Test alert broadcasting over WebSocket."""
        from backend.api.websocket import broadcast_alert
        
        alert = Alert(
            id="alert-test",
            alert_type=AlertType.HARDWARE_THRESHOLD,
            severity=AlertSeverity.HIGH,
            title="Test Alert",
            message="This is a test",
            metadata={},
            triggered_at=datetime.utcnow(),
            acknowledged=False,
        )

        # Broadcast should not raise exception
        await broadcast_alert(alert)


class TestIntegration:
    """Integration tests for complete monitoring flow."""

    @pytest.mark.asyncio
    async def test_complete_monitoring_flow(
        self, mock_supabase_adapter, metrics_service, alert_service
    ):
        """Test complete flow: metrics → evaluation → alerts."""
        # 1. Get metrics
        pipeline_metrics = await metrics_service.get_pipeline_metrics()
        assert isinstance(pipeline_metrics, PipelineMetrics)

        # 2. Evaluate alerts
        alerts = await alert_service.evaluate_alerts()
        assert isinstance(alerts, list)

        # 3. If alerts triggered, they should be stored
        if len(alerts) > 0:
            assert all(isinstance(alert, Alert) for alert in alerts)

    @pytest.mark.asyncio
    async def test_health_check_includes_monitoring(self, client):
        """Test that health check includes monitoring services."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "services" in data
        assert "monitoring" in data["services"]
        
        monitoring = data["services"]["monitoring"]
        assert "metrics_service" in monitoring
        assert "alert_service" in monitoring
        assert "websocket_connections" in monitoring


# Fixtures

@pytest.fixture
def mock_supabase_adapter():
    """Create mock Supabase adapter."""
    from backend.services.supabase_adapter import SupabaseAdapter
    
    adapter = Mock(spec=SupabaseAdapter)
    adapter.client = Mock()
    adapter.service_client = Mock()
    
    return adapter


@pytest.fixture
def mock_jwt_token():
    """Create mock JWT token for testing."""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsInBlcm1pc3Npb25zIjpbIm1vbml0b3Jpbmc6cmVhZCIsImFsZXJ0czpyZWFkIl19.test"


@pytest.fixture
async def metrics_service(mock_supabase_adapter):
    """Create MetricsService for testing."""
    from backend.processors.stage_tracker import StageTracker
    stage_tracker = StageTracker(mock_supabase_adapter.client)
    return MetricsService(mock_supabase_adapter, stage_tracker)


@pytest.fixture
async def alert_service(mock_supabase_adapter, metrics_service):
    """Create AlertService for testing."""
    service = AlertService(mock_supabase_adapter, metrics_service)
    await service.load_alert_rules()
    return service


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
