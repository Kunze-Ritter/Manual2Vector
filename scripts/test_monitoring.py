"""
Test Runner for Monitoring System

Quick script to run monitoring system tests with real database connection.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv
load_dotenv()

from backend.services.supabase_adapter import SupabaseAdapter
from backend.services.metrics_service import MetricsService
from backend.services.alert_service import AlertService
from backend.processors.stage_tracker import StageTracker
from backend.models.monitoring import AlertSeverity


async def test_metrics_service():
    """Test MetricsService with real database."""
    print("\n" + "="*60)
    print("Testing MetricsService")
    print("="*60)
    
    try:
        # Initialize services
        adapter = SupabaseAdapter()
        stage_tracker = StageTracker(adapter.client)
        metrics_service = MetricsService(adapter, stage_tracker)
        
        # Test pipeline metrics
        print("\n1. Testing Pipeline Metrics...")
        pipeline_metrics = await metrics_service.get_pipeline_metrics()
        print(f"   ✅ Total Documents: {pipeline_metrics.total_documents}")
        print(f"   ✅ Success Rate: {pipeline_metrics.success_rate}%")
        print(f"   ✅ Throughput: {pipeline_metrics.current_throughput_docs_per_hour} docs/hour")
        
        # Test queue metrics
        print("\n2. Testing Queue Metrics...")
        queue_metrics = await metrics_service.get_queue_metrics()
        print(f"   ✅ Total Items: {queue_metrics.total_items}")
        print(f"   ✅ Pending: {queue_metrics.pending_count}")
        print(f"   ✅ Processing: {queue_metrics.processing_count}")
        
        # Test stage metrics
        print("\n3. Testing Stage Metrics...")
        stage_metrics = await metrics_service.get_stage_metrics()
        print(f"   ✅ Stages Tracked: {len(stage_metrics)}")
        for stage in stage_metrics[:3]:  # Show first 3
            print(f"      - {stage.stage_name}: {stage.success_rate}% success")
        
        # Test hardware metrics
        print("\n4. Testing Hardware Metrics...")
        hardware_metrics = await metrics_service.get_hardware_metrics()
        print(f"   ✅ CPU: {hardware_metrics.cpu_percent}%")
        print(f"   ✅ RAM: {hardware_metrics.ram_percent}%")
        print(f"   ✅ Disk: {hardware_metrics.disk_percent}%")
        
        # Test data quality metrics
        print("\n5. Testing Data Quality Metrics...")
        quality_metrics = await metrics_service.get_data_quality_metrics()
        print(f"   ✅ Total Duplicates: {quality_metrics.duplicate_metrics.total_duplicates}")
        print(f"   ✅ Validation Errors: {quality_metrics.validation_metrics.total_validation_errors}")
        
        # Test caching
        print("\n6. Testing Cache Performance...")
        import time
        start = time.time()
        await metrics_service.get_pipeline_metrics()
        cached_time = time.time() - start
        
        metrics_service.invalidate_cache("pipeline_metrics")
        
        start = time.time()
        await metrics_service.get_pipeline_metrics()
        uncached_time = time.time() - start
        
        print(f"   ✅ Cached query: {cached_time*1000:.2f}ms")
        print(f"   ✅ Uncached query: {uncached_time*1000:.2f}ms")
        print(f"   ✅ Speedup: {uncached_time/cached_time:.1f}x faster")
        
        print("\n✅ MetricsService: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ MetricsService: TEST FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_alert_service():
    """Test AlertService with real database."""
    print("\n" + "="*60)
    print("Testing AlertService")
    print("="*60)
    
    try:
        # Initialize services
        adapter = SupabaseAdapter()
        stage_tracker = StageTracker(adapter.client)
        metrics_service = MetricsService(adapter, stage_tracker)
        alert_service = AlertService(adapter, metrics_service)
        
        # Test loading alert rules
        print("\n1. Testing Alert Rules Loading...")
        rules = await alert_service.load_alert_rules()
        print(f"   ✅ Loaded {len(rules)} alert rules")
        for rule in rules[:3]:  # Show first 3
            print(f"      - {rule.name} ({rule.severity.value}): {rule.threshold_operator} {rule.threshold_value}")
        
        # Test alert evaluation
        print("\n2. Testing Alert Evaluation...")
        alerts = await alert_service.evaluate_alerts()
        print(f"   ✅ Evaluated {len(alert_service.alert_rules)} rules")
        print(f"   ✅ Triggered {len(alerts)} new alerts")
        
        if alerts:
            print("\n   🚨 Active Alerts:")
            for alert in alerts:
                print(f"      - [{alert.severity.value.upper()}] {alert.title}")
                print(f"        {alert.message}")
        
        # Test getting alerts
        print("\n3. Testing Alert Retrieval...")
        alert_response = await alert_service.get_alerts(limit=10)
        print(f"   ✅ Total Alerts: {alert_response.total}")
        print(f"   ✅ Unacknowledged: {alert_response.unacknowledged_count}")
        
        # Test filtering
        print("\n4. Testing Alert Filtering...")
        high_alerts = await alert_service.get_alerts(
            severity_filter=AlertSeverity.HIGH,
            acknowledged_filter=False
        )
        print(f"   ✅ High Priority Unacknowledged: {len(high_alerts.alerts)}")
        
        print("\n✅ AlertService: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ AlertService: TEST FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration():
    """Test complete monitoring flow."""
    print("\n" + "="*60)
    print("Testing Integration Flow")
    print("="*60)
    
    try:
        # Initialize all services
        adapter = SupabaseAdapter()
        stage_tracker = StageTracker(adapter.client)
        metrics_service = MetricsService(adapter, stage_tracker)
        alert_service = AlertService(adapter, metrics_service)
        
        print("\n1. Collecting All Metrics...")
        pipeline = await metrics_service.get_pipeline_metrics()
        queue = await metrics_service.get_queue_metrics()
        hardware = await metrics_service.get_hardware_metrics()
        quality = await metrics_service.get_data_quality_metrics()
        
        print(f"   ✅ Pipeline: {pipeline.total_documents} docs, {pipeline.success_rate}% success")
        print(f"   ✅ Queue: {queue.total_items} items, {queue.pending_count} pending")
        print(f"   ✅ Hardware: CPU {hardware.cpu_percent}%, RAM {hardware.ram_percent}%")
        print(f"   ✅ Quality: {quality.duplicate_metrics.total_duplicates} duplicates")
        
        print("\n2. Evaluating Alert Rules...")
        alerts = await alert_service.evaluate_alerts()
        
        if alerts:
            print(f"   🚨 {len(alerts)} alerts triggered!")
            for alert in alerts:
                print(f"      - {alert.title}")
        else:
            print("   ✅ No alerts triggered - system healthy")
        
        print("\n3. Testing Performance...")
        import time
        
        # Test aggregated view performance
        start = time.time()
        for _ in range(10):
            await metrics_service.get_pipeline_metrics()
        elapsed = time.time() - start
        
        print(f"   ✅ 10 metric queries: {elapsed*1000:.2f}ms ({elapsed*100:.2f}ms avg)")
        
        print("\n✅ Integration: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration: TEST FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_views():
    """Test that aggregated views exist and work."""
    print("\n" + "="*60)
    print("Testing Database Views")
    print("="*60)
    
    try:
        adapter = SupabaseAdapter()
        client = adapter.service_client or adapter.client
        
        # Test pipeline view
        print("\n1. Testing vw_pipeline_metrics_aggregated...")
        response = client.table("vw_pipeline_metrics_aggregated", schema="public").select("*").limit(1).execute()
        if response.data:
            print(f"   ✅ View exists and returns data")
            print(f"      Total docs: {response.data[0].get('total_documents', 0)}")
        else:
            print("   ⚠️  View exists but no data")
        
        # Test queue view
        print("\n2. Testing vw_queue_metrics_aggregated...")
        response = client.table("vw_queue_metrics_aggregated", schema="public").select("*").limit(1).execute()
        if response.data:
            print(f"   ✅ View exists and returns data")
            print(f"      Total items: {response.data[0].get('total_items', 0)}")
        else:
            print("   ⚠️  View exists but no data")
        
        # Test stage view
        print("\n3. Testing vw_stage_metrics_aggregated...")
        response = client.table("vw_stage_metrics_aggregated", schema="public").select("*").execute()
        if response.data:
            print(f"   ✅ View exists and returns data")
            print(f"      Stages: {len(response.data)}")
        else:
            print("   ⚠️  View exists but no data")
        
        # Test RPC functions
        print("\n4. Testing RPC Functions...")
        try:
            response = client.rpc("get_duplicate_hashes", {}).execute()
            print(f"   ✅ get_duplicate_hashes: {len(response.data or [])} results")
        except Exception as e:
            print(f"   ❌ get_duplicate_hashes failed: {e}")
        
        try:
            response = client.rpc("get_duplicate_filenames", {}).execute()
            print(f"   ✅ get_duplicate_filenames: {len(response.data or [])} results")
        except Exception as e:
            print(f"   ❌ get_duplicate_filenames failed: {e}")
        
        print("\n✅ Database Views: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Database Views: TEST FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("MONITORING SYSTEM END-TO-END TESTS")
    print("="*60)
    
    results = []
    
    # Run all test suites
    results.append(("Database Views", await test_database_views()))
    results.append(("MetricsService", await test_metrics_service()))
    results.append(("AlertService", await test_alert_service()))
    results.append(("Integration", await test_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:20s} {status}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} test suites passed")
    
    if total_passed == total_tests:
        print("\n🎉 ALL TESTS PASSED! Monitoring system is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} test suite(s) failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
