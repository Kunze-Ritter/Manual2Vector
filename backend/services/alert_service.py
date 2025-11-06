"""Alert system service for monitoring."""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.models.monitoring import Alert, AlertListResponse, AlertRule, AlertSeverity, AlertType, CreateAlertRule
from backend.services.metrics_service import MetricsService
from backend.services.supabase_adapter import SupabaseAdapter

LOGGER = logging.getLogger(__name__)


class AlertService:
    """Service for managing alerts and alert rules."""

    def __init__(self, supabase_adapter: SupabaseAdapter, metrics_service: MetricsService):
        """Initialize alert service."""
        self.adapter = supabase_adapter
        self.metrics_service = metrics_service
        self.alert_rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.logger = LOGGER

    async def load_alert_rules(self) -> List[AlertRule]:
        """Load alert rules from database or use defaults."""
        try:
            client = self.adapter.service_client or self.adapter.client
            if not client:
                raise RuntimeError("Supabase client not available")

            # Try to load from database
            response = client.table("alert_rules", schema="krai_system").select("*").eq("enabled", True).execute()
            
            if response.data:
                self.alert_rules = [
                    AlertRule(
                        id=str(rule.get("id", "")),
                        name=rule.get("name", ""),
                        alert_type=AlertType(rule.get("alert_type", "system_error")),
                        severity=AlertSeverity(rule.get("severity", "medium")),
                        threshold_value=float(rule.get("threshold_value", 0.0)),
                        threshold_operator=rule.get("threshold_operator", ">"),
                        metric_key=rule.get("metric_key"),
                        enabled=rule.get("enabled", True),
                    )
                    for rule in response.data
                ]
            else:
                # Use default rules
                self.alert_rules = self._get_default_rules()
            
            self.logger.info(f"Loaded {len(self.alert_rules)} alert rules")
            return self.alert_rules

        except Exception as e:
            self.logger.error(f"Failed to load alert rules: {e}", exc_info=True)
            # Use default rules on error
            self.alert_rules = self._get_default_rules()
            return self.alert_rules

    def _get_default_rules(self) -> List[AlertRule]:
        """Get default alert rules."""
        return [
            AlertRule(
                id=str(uuid.uuid4()),
                name="High Processing Failure Rate",
                alert_type=AlertType.PROCESSING_FAILURE,
                severity=AlertSeverity.HIGH,
                threshold_value=10.0,
                threshold_operator=">",
                enabled=True,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="Queue Overflow",
                alert_type=AlertType.QUEUE_OVERFLOW,
                severity=AlertSeverity.MEDIUM,
                threshold_value=100.0,
                threshold_operator=">",
                metric_key="queue_overflow",
                enabled=True,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="High CPU Usage",
                alert_type=AlertType.HARDWARE_THRESHOLD,
                severity=AlertSeverity.HIGH,
                threshold_value=90.0,
                threshold_operator=">",
                metric_key="cpu",
                enabled=True,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="High RAM Usage",
                alert_type=AlertType.HARDWARE_THRESHOLD,
                severity=AlertSeverity.HIGH,
                threshold_value=90.0,
                threshold_operator=">",
                metric_key="ram",
                enabled=True,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="High Duplicate Count",
                alert_type=AlertType.DATA_QUALITY,
                severity=AlertSeverity.MEDIUM,
                threshold_value=50.0,
                threshold_operator=">",
                metric_key="duplicates",
                enabled=True,
            ),
            AlertRule(
                id=str(uuid.uuid4()),
                name="High Validation Errors",
                alert_type=AlertType.DATA_QUALITY,
                severity=AlertSeverity.MEDIUM,
                threshold_value=20.0,
                threshold_operator=">",
                metric_key="validation_errors",
                enabled=True,
            ),
        ]

    async def add_alert_rule(self, rule: CreateAlertRule) -> str:
        """Add new alert rule."""
        try:
            client = self.adapter.service_client or self.adapter.client
            if not client:
                raise RuntimeError("Supabase client not available")

            rule_data = {
                "name": rule.name,
                "alert_type": rule.alert_type.value,
                "severity": rule.severity.value,
                "threshold_value": rule.threshold_value,
                "threshold_operator": rule.threshold_operator,
                "metric_key": rule.metric_key,
                "enabled": rule.enabled,
            }

            response = client.table("alert_rules", schema="krai_system").insert(rule_data).execute()
            
            if response.data:
                rule_id = str(response.data[0].get("id", ""))
                await self.load_alert_rules()
                self.logger.info(f"Added alert rule: {rule.name} (ID: {rule_id})")
                return rule_id
            
            raise RuntimeError("Failed to insert alert rule")

        except Exception as e:
            self.logger.error(f"Failed to add alert rule: {e}", exc_info=True)
            raise

    async def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing alert rule."""
        try:
            client = self.adapter.service_client or self.adapter.client
            if not client:
                raise RuntimeError("Supabase client not available")

            response = client.table("alert_rules", schema="krai_system").update(updates).eq("id", rule_id).execute()
            
            if response.data:
                await self.load_alert_rules()
                self.logger.info(f"Updated alert rule: {rule_id}")
                return True
            
            return False

        except Exception as e:
            self.logger.error(f"Failed to update alert rule: {e}", exc_info=True)
            return False

    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete alert rule."""
        try:
            client = self.adapter.service_client or self.adapter.client
            if not client:
                raise RuntimeError("Supabase client not available")

            response = client.table("alert_rules", schema="krai_system").delete().eq("id", rule_id).execute()
            
            if response.data:
                await self.load_alert_rules()
                self.logger.info(f"Deleted alert rule: {rule_id}")
                return True
            
            return False

        except Exception as e:
            self.logger.error(f"Failed to delete alert rule: {e}", exc_info=True)
            return False

    def _check_threshold(self, rule: AlertRule, current_value: float) -> bool:
        """Check if threshold is exceeded."""
        operator = rule.threshold_operator
        threshold = rule.threshold_value

        if operator == ">":
            return current_value > threshold
        elif operator == "<":
            return current_value < threshold
        elif operator == "==":
            return current_value == threshold
        elif operator == ">=":
            return current_value >= threshold
        elif operator == "<=":
            return current_value <= threshold
        else:
            self.logger.warning(f"Unknown operator: {operator}")
            return False

    async def _create_alert(self, rule: AlertRule, current_value: float, metadata: Dict[str, Any]) -> Alert:
        """Create new alert."""
        try:
            alert_id = str(uuid.uuid4())
            
            # Generate title and message
            title = f"{rule.name}"
            message = f"{rule.name}: Current value is {current_value}, exceeding threshold of {rule.threshold_value}"

            alert = Alert(
                id=alert_id,
                alert_type=rule.alert_type,
                severity=rule.severity,
                title=title,
                message=message,
                metadata={
                    "rule_id": rule.id,
                    "current_value": current_value,
                    "threshold": rule.threshold_value,
                    "operator": rule.threshold_operator,
                    **metadata,
                },
                triggered_at=datetime.utcnow(),
                acknowledged=False,
            )

            # Insert into database
            client = self.adapter.service_client or self.adapter.client
            if client:
                alert_data = {
                    "id": alert_id,
                    "alert_type": alert.alert_type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "message": alert.message,
                    "metadata": alert.metadata,
                    "triggered_at": alert.triggered_at.isoformat(),
                }
                client.table("alerts", schema="krai_system").insert(alert_data).execute()

            self.logger.info(f"Created alert: {title} (ID: {alert_id})")
            return alert

        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}", exc_info=True)
            raise

    async def evaluate_alerts(self) -> List[Alert]:
        """Evaluate alert rules and create alerts if needed."""
        new_alerts: List[Alert] = []

        try:
            # Get current metrics
            pipeline_metrics = await self.metrics_service.get_pipeline_metrics()
            queue_metrics = await self.metrics_service.get_queue_metrics()
            hardware_metrics = await self.metrics_service.get_hardware_metrics()
            data_quality = await self.metrics_service.get_data_quality_metrics()

            # Evaluate each rule
            for rule in self.alert_rules:
                if not rule.enabled:
                    continue

                current_value = 0.0
                metadata: Dict[str, Any] = {}

                # Determine current value based on alert type
                if rule.alert_type == AlertType.PROCESSING_FAILURE:
                    current_value = 100.0 - pipeline_metrics.success_rate
                    metadata = {"success_rate": pipeline_metrics.success_rate}
                
                elif rule.alert_type == AlertType.QUEUE_OVERFLOW:
                    current_value = float(queue_metrics.pending_count)
                    metadata = {"pending_count": queue_metrics.pending_count}
                
                elif rule.alert_type == AlertType.HARDWARE_THRESHOLD:
                    # Use metric_key for precise metric selection
                    if rule.metric_key == "cpu":
                        current_value = hardware_metrics.cpu_percent
                        metadata = {"cpu_percent": hardware_metrics.cpu_percent}
                    elif rule.metric_key == "ram":
                        current_value = hardware_metrics.ram_percent
                        metadata = {"ram_percent": hardware_metrics.ram_percent}
                    else:
                        # Fallback to name-based detection for backward compatibility
                        if "CPU" in rule.name.upper():
                            current_value = hardware_metrics.cpu_percent
                            metadata = {"cpu_percent": hardware_metrics.cpu_percent}
                        elif "RAM" in rule.name.upper():
                            current_value = hardware_metrics.ram_percent
                            metadata = {"ram_percent": hardware_metrics.ram_percent}
                
                elif rule.alert_type == AlertType.DATA_QUALITY:
                    # Use metric_key for precise metric selection
                    if rule.metric_key == "duplicates":
                        current_value = float(data_quality.duplicate_metrics.total_duplicates)
                        metadata = {"total_duplicates": data_quality.duplicate_metrics.total_duplicates}
                    elif rule.metric_key == "validation_errors":
                        current_value = float(data_quality.validation_metrics.total_validation_errors)
                        metadata = {"total_errors": data_quality.validation_metrics.total_validation_errors}
                    else:
                        # Fallback to name-based detection for backward compatibility
                        if "DUPLICATE" in rule.name.upper():
                            current_value = float(data_quality.duplicate_metrics.total_duplicates)
                            metadata = {"total_duplicates": data_quality.duplicate_metrics.total_duplicates}
                        elif "VALIDATION" in rule.name.upper():
                            current_value = float(data_quality.validation_metrics.total_validation_errors)
                            metadata = {"total_errors": data_quality.validation_metrics.total_validation_errors}

                # Check threshold
                if self._check_threshold(rule, current_value):
                    # Check if alert already active
                    if rule.id not in self.active_alerts:
                        alert = await self._create_alert(rule, current_value, metadata)
                        self.active_alerts[rule.id] = alert
                        new_alerts.append(alert)
                else:
                    # Remove from active alerts if threshold no longer exceeded
                    self.active_alerts.pop(rule.id, None)

        except Exception as e:
            self.logger.error(f"Failed to evaluate alerts: {e}", exc_info=True)

        return new_alerts

    async def get_alerts(
        self,
        limit: int = 50,
        severity_filter: Optional[AlertSeverity] = None,
        acknowledged_filter: Optional[bool] = None,
    ) -> AlertListResponse:
        """Get alerts with optional filtering."""
        try:
            client = self.adapter.service_client or self.adapter.client
            if not client:
                raise RuntimeError("Supabase client not available")

            # Build query
            query = client.table("alerts", schema="krai_system").select("*")
            
            if severity_filter:
                query = query.eq("severity", severity_filter.value)
            
            if acknowledged_filter is not None:
                query = query.eq("acknowledged", acknowledged_filter)
            
            query = query.order("triggered_at", desc=True).limit(limit)
            
            response = query.execute()
            alerts_data = response.data or []

            alerts = [
                Alert(
                    id=str(alert.get("id", "")),
                    alert_type=AlertType(alert.get("alert_type", "system_error")),
                    severity=AlertSeverity(alert.get("severity", "medium")),
                    title=alert.get("title", ""),
                    message=alert.get("message", ""),
                    metadata=alert.get("metadata", {}),
                    triggered_at=datetime.fromisoformat(alert["triggered_at"].replace("Z", "+00:00")) if alert.get("triggered_at") else datetime.utcnow(),
                    acknowledged=alert.get("acknowledged", False),
                    acknowledged_at=datetime.fromisoformat(alert["acknowledged_at"].replace("Z", "+00:00")) if alert.get("acknowledged_at") else None,
                    acknowledged_by=alert.get("acknowledged_by"),
                )
                for alert in alerts_data
            ]

            # Count unacknowledged
            unack_response = client.table("alerts", schema="krai_system").select("id", count="exact").eq("acknowledged", False).execute()
            unacknowledged_count = unack_response.count or 0

            return AlertListResponse(
                alerts=alerts,
                total=len(alerts),
                unacknowledged_count=unacknowledged_count,
            )

        except Exception as e:
            self.logger.error(f"Failed to get alerts: {e}", exc_info=True)
            return AlertListResponse(alerts=[], total=0, unacknowledged_count=0)

    async def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge an alert."""
        try:
            client = self.adapter.service_client or self.adapter.client
            if not client:
                raise RuntimeError("Supabase client not available")

            update_data = {
                "acknowledged": True,
                "acknowledged_at": datetime.utcnow().isoformat(),
                "acknowledged_by": user_id,
            }

            response = client.table("alerts", schema="krai_system").update(update_data).eq("id", alert_id).execute()
            
            if response.data:
                # Remove from active alerts
                for rule_id, alert in list(self.active_alerts.items()):
                    if alert.id == alert_id:
                        del self.active_alerts[rule_id]
                        break
                
                self.logger.info(f"Acknowledged alert: {alert_id} by user {user_id}")
                return True
            
            return False

        except Exception as e:
            self.logger.error(f"Failed to acknowledge alert: {e}", exc_info=True)
            return False

    async def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss (delete) an alert."""
        try:
            client = self.adapter.service_client or self.adapter.client
            if not client:
                raise RuntimeError("Supabase client not available")

            response = client.table("alerts", schema="krai_system").delete().eq("id", alert_id).execute()
            
            if response.data:
                # Remove from active alerts
                for rule_id, alert in list(self.active_alerts.items()):
                    if alert.id == alert_id:
                        del self.active_alerts[rule_id]
                        break
                
                self.logger.info(f"Dismissed alert: {alert_id}")
                return True
            
            return False

        except Exception as e:
            self.logger.error(f"Failed to dismiss alert: {e}", exc_info=True)
            return False

    async def notify_alert(self, alert: Alert) -> None:
        """Notify about alert (placeholder for external notifications)."""
        # Log alert
        self.logger.warning(
            f"ALERT TRIGGERED: [{alert.severity.value.upper()}] {alert.title} - {alert.message}"
        )
        
        # Broadcast over WebSocket
        try:
            from backend.api.websocket import broadcast_alert
            await broadcast_alert(alert)
        except Exception as e:
            self.logger.error(f"Failed to broadcast alert via WebSocket: {e}")

    async def start_alert_monitoring(self, interval_seconds: int = 60) -> None:
        """Start background alert monitoring loop."""
        self.logger.info(f"Starting alert monitoring (interval: {interval_seconds}s)")
        
        # Load rules on startup
        await self.load_alert_rules()

        while True:
            try:
                await asyncio.sleep(interval_seconds)
                
                # Evaluate alerts
                new_alerts = await self.evaluate_alerts()
                
                # Notify about new alerts
                for alert in new_alerts:
                    await self.notify_alert(alert)
                
                if new_alerts:
                    self.logger.info(f"Evaluated alerts: {len(new_alerts)} new alerts triggered")

            except asyncio.CancelledError:
                self.logger.info("Alert monitoring stopped")
                break
            except Exception as e:
                self.logger.error(f"Error in alert monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(interval_seconds)
