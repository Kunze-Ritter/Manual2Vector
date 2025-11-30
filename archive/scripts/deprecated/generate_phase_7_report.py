#!/usr/bin/env python3
"""
KRAI Phase 7 Validation Report Generator
========================================

Comprehensive validation report generator for Phase 1-6 features.
This script orchestrates all Phase 7 validation scripts, collects their outputs,
and generates a consolidated HTML report and JSON summary for stakeholders.

Features:
- Orchestrates all Phase 7 validation scripts
- Collects and normalizes test results
- Generates HTML report with Jinja2 templates
- Creates JSON summary for programmatic access
- Provides console summary with rich formatting
- Tracks performance metrics and recommendations

Usage:
    python scripts/generate_phase_7_report.py
    python scripts/generate_phase_7_report.py --verbose
    python scripts/generate_phase_7_report.py --output-dir custom_reports
"""

import os
import sys
import asyncio
import argparse
import json
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich import box
    from rich.syntax import Syntax
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from jinja2 import Template
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

# Test script imports
try:
    from scripts.test_full_pipeline_phases_1_6 import FullPipelineTestRunner
    from scripts.test_hierarchical_chunking import HierarchicalChunkingTester
    from scripts.test_svg_extraction import SVGExtractionTester
    from scripts.test_multimodal_search import MultimodalSearchTester
    from scripts.test_minio_storage_operations import MinIOStorageTester
    from scripts.test_postgresql_migrations import PostgreSQLMigrationTester
    from scripts.test_context_extraction_integration import ContextExtractionIntegrationTester
    TEST_SCRIPTS_AVAILABLE = True
except ImportError as e:
    TEST_SCRIPTS_AVAILABLE = False
    IMPORT_ERROR = str(e)

@dataclass
class TestSectionResult:
    """Normalized result for a test section"""
    name: str
    success: bool
    duration_ms: float
    details: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    critical: bool = False

@dataclass
class Phase7Report:
    """Complete Phase 7 validation report"""
    timestamp: str
    environment: Dict[str, Any]
    summary: Dict[str, Any]
    sections: List[TestSectionResult]
    recommendations: List[str]
    overall_success: bool

class Phase7ReportGenerator:
    """Generates comprehensive Phase 7 validation reports"""
    
    def __init__(self, verbose: bool = False, output_dir: str = "reports/phase7"):
        self.verbose = verbose
        self.output_dir = Path(output_dir)
        self.console = Console() if RICH_AVAILABLE else None
        self.logger = logging.getLogger("krai.phase7_report_generator")
        
        # Test configuration
        self.test_sections = [
            {
                "name": "Full Pipeline Integration",
                "class": FullPipelineTestRunner,
                "method": "run_all_tests",
                "critical": True,
                "description": "End-to-end pipeline validation"
            },
            {
                "name": "Hierarchical Chunking",
                "class": HierarchicalChunkingTester,
                "method": "run_all_tests",
                "critical": False,
                "description": "Document structure detection and chunking"
            },
            {
                "name": "SVG Extraction",
                "class": SVGExtractionTester,
                "method": "run_all_tests",
                "critical": False,
                "description": "Vector graphics processing and conversion"
            },
            {
                "name": "Multimodal Search",
                "class": MultimodalSearchTester,
                "method": "run_all_tests",
                "critical": False,
                "description": "Unified search across content types"
            },
            {
                "name": "MinIO Storage Operations",
                "class": MinIOStorageTester,
                "method": "run_all_tests",
                "critical": True,
                "description": "Object storage functionality"
            },
            {
                "name": "PostgreSQL Migrations",
                "class": PostgreSQLMigrationTester,
                "method": "run_all_tests",
                "critical": True,
                "description": "Database schema and migrations"
            },
            {
                "name": "Context Extraction Integration",
                "class": ContextExtractionIntegrationTester,
                "method": "run_all_tests",
                "critical": False,
                "description": "AI-powered context extraction"
            }
        ]
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def print_status(self, message: str, status: str = 'info'):
        """Print status message with appropriate formatting"""
        if self.console:
            color = {
                'success': 'green',
                'warning': 'yellow',
                'error': 'red',
                'info': 'blue',
                'test': 'cyan',
                'report': 'purple'
            }.get(status, 'white')
            
            icon = {
                'success': '✅',
                'warning': '⚠️',
                'error': '❌',
                'info': 'ℹ️',
                'test': '🧪',
                'report': '📊'
            }.get(status, '•')
            
            self.console.print(f"{icon} {message}", style=color)
        else:
            print(f"{message}")
    
    async def setup(self) -> bool:
        """Initialize report generation environment"""
        try:
            self.print_status("Setting up Phase 7 Report Generator", 'report')
            
            # Check dependencies
            if not TEST_SCRIPTS_AVAILABLE:
                self.print_status(f"Test scripts not available: {IMPORT_ERROR}", 'error')
                return False
            
            # Load environment
            env_file = ".env.test" if Path(".env.test").exists() else ".env"
            from dotenv import load_dotenv
            load_dotenv(env_file)
            self.print_status(f"Loaded environment from {env_file}", 'info')
            
            # Create output directory
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.print_status(f"Output directory: {self.output_dir}", 'info')
            
            # Get version info
            self.version_info = await self._get_version_info()
            
            self.print_status("Setup completed successfully", 'success')
            return True
            
        except Exception as e:
            self.print_status(f"Setup failed: {e}", 'error')
            self.logger.error("Setup failed", exc_info=True)
            return False
    
    async def _get_version_info(self) -> Dict[str, Any]:
        """Get version and environment information"""
        version_info = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": sys.version,
            "platform": sys.platform
        }
        
        # Try to get backend version
        try:
            backend_version_path = Path("backend/processors/__version__.py")
            if backend_version_path.exists():
                with open(backend_version_path, 'r') as f:
                    version_content = f.read()
                    # Extract version from the file
                    for line in version_content.split('\n'):
                        if line.startswith('__version__'):
                            version_info["krai_version"] = line.split('=')[1].strip().strip('"\'')
                            break
        except Exception:
            version_info["krai_version"] = "unknown"
        
        # Environment variables
        version_info["environment"] = {
            "ollama_base_url": os.getenv("OLLAMA_BASE_URL", "not_set"),
            "database_url": "set" if os.getenv("DATABASE_URL") else "not_set",
            "minio_endpoint": os.getenv("MINIO_ENDPOINT", "not_set"),
            "log_level": os.getenv("LOG_LEVEL", "INFO")
        }
        
        return version_info
    
    async def run_test_section(self, section_config: Dict[str, Any]) -> TestSectionResult:
        """Run a single test section and normalize results"""
        section_name = section_config["name"]
        self.print_status(f"Running test section: {section_name}", 'test')
        
        start_time = time.time()
        
        try:
            # Initialize test runner
            test_class = section_config["class"]
            test_runner = test_class(verbose=self.verbose)
            
            # Run the test
            test_method = getattr(test_runner, section_config["method"])
            raw_result = await test_method()
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Normalize result
            if isinstance(raw_result, dict):
                success = raw_result.get('success', False)
                details = raw_result
                
                # Extract common metrics
                if 'total_tests' in raw_result:
                    details['test_summary'] = {
                        'total': raw_result.get('total_tests', 0),
                        'passed': raw_result.get('passed', 0),
                        'failed': raw_result.get('failed', 0),
                        'skipped': raw_result.get('skipped', 0)
                    }
                
                errors = raw_result.get('errors', [])
                warnings = raw_result.get('warnings', [])
                
            else:
                success = bool(raw_result)
                details = {"raw_result": str(raw_result)}
                errors = []
                warnings = []
            
            result = TestSectionResult(
                name=section_name,
                success=success,
                duration_ms=duration_ms,
                details=details,
                errors=errors if isinstance(errors, list) else [str(errors)],
                warnings=warnings if isinstance(warnings, list) else [str(warnings)],
                critical=section_config.get("critical", False)
            )
            
            status = 'success' if success else 'error'
            self.print_status(f"{section_name}: {'✅ PASSED' if success else '❌ FAILED'} ({duration_ms:.2f}ms)", status)
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Test section failed: {str(e)}"
            
            self.print_status(f"{section_name}: ❌ EXCEPTION ({duration_ms:.2f}ms)", 'error')
            if self.verbose:
                self.print_status(f"  Error: {error_msg}", 'error')
                self.print_status(f"  Traceback: {traceback.format_exc()}", 'error')
            
            return TestSectionResult(
                name=section_name,
                success=False,
                duration_ms=duration_ms,
                details={"exception": str(e), "traceback": traceback.format_exc()},
                errors=[error_msg],
                warnings=[],
                critical=section_config.get("critical", False)
            )
    
    async def run_all_tests(self) -> List[TestSectionResult]:
        """Run all test sections"""
        self.print_status("Running all Phase 7 test sections...", 'test')
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Running tests...", total=len(self.test_sections))
            
            for section_config in self.test_sections:
                progress.update(task, description=section_config["name"])
                
                result = await self.run_test_section(section_config)
                results.append(result)
                
                progress.advance(task)
        
        return results
    
    def generate_recommendations(self, results: List[TestSectionResult]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze failed sections
        failed_sections = [r for r in results if not r.success]
        critical_failures = [r for r in failed_sections if r.critical]
        
        if critical_failures:
            recommendations.append("🚨 CRITICAL: Address critical failures in: " + 
                                 ", ".join([r.name for r in critical_failures]))
        
        if failed_sections:
            recommendations.append("⚠️ Review and fix failed test sections: " + 
                                 ", ".join([r.name for r in failed_sections]))
        
        # Performance recommendations
        slow_sections = [r for r in results if r.duration_ms > 30000]  # > 30 seconds
        if slow_sections:
            recommendations.append("⏱️ Performance optimization needed for: " + 
                                 ", ".join([f"{r.name} ({r.duration_ms/1000:.1f}s)" for r in slow_sections]))
        
        # Feature-specific recommendations
        svg_result = next((r for r in results if "SVG" in r.name), None)
        if svg_result and not svg_result.success:
            recommendations.append("🎨 Check SVG processing libraries (Pillow, svglib, reportlab)")
        
        search_result = next((r for r in results if "Search" in r.name), None)
        if search_result and not search_result.success:
            recommendations.append("🔍 Verify embedding models and search configuration")
        
        # Success recommendations
        if all(r.success for r in results):
            recommendations.append("🎉 All tests passed! System is ready for production.")
            recommendations.append("📈 Consider running performance tests for load validation.")
        
        return recommendations
    
    def calculate_summary(self, results: List[TestSectionResult]) -> Dict[str, Any]:
        """Calculate overall summary statistics"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.success)
        failed_tests = total_tests - passed_tests
        critical_failed = sum(1 for r in results if not r.success and r.critical)
        
        total_duration = sum(r.duration_ms for r in results)
        
        # Aggregate test counts from individual sections
        aggregate_totals = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        for result in results:
            if "test_summary" in result.details:
                summary = result.details["test_summary"]
                for key in aggregate_totals:
                    aggregate_totals[key] += summary.get(key, 0)
        
        return {
            "total_sections": total_tests,
            "passed_sections": passed_tests,
            "failed_sections": failed_tests,
            "critical_failures": critical_failed,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_duration_ms": total_duration,
            "aggregate_test_totals": aggregate_totals,
            "overall_success": critical_failed == 0 and passed_tests > 0
        }
    
    def generate_html_report(self, report: Phase7Report) -> str:
        """Generate HTML report using Jinja2 template"""
        if not JINJA2_AVAILABLE:
            return self._generate_simple_html_report(report)
        
        template_str = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KRAI Phase 7 Validation Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; }
        .content { padding: 30px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .metric { background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }
        .metric-value { font-size: 2em; font-weight: bold; color: #333; }
        .metric-label { color: #666; margin-top: 5px; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        .section { margin-bottom: 30px; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden; }
        .section-header { background: #f8f9fa; padding: 15px 20px; font-weight: bold; display: flex; justify-content: space-between; align-items: center; }
        .section-content { padding: 20px; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
        .status-passed { background: #d4edda; color: #155724; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .status-critical { background: #f5c6cb; color: #721c24; }
        .recommendations { background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 20px; }
        .recommendations h3 { color: #856404; margin-top: 0; }
        .recommendations ul { margin: 0; padding-left: 20px; }
        .details-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
        .detail-item { background: #f8f9fa; padding: 15px; border-radius: 6px; }
        .detail-label { font-weight: bold; color: #666; }
        .detail-value { color: #333; }
        @media (max-width: 768px) { .summary { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 KRAI Phase 7 Validation Report</h1>
            <p>Generated on {{ timestamp }} • Version: {{ version_info.krai_version }}</p>
        </div>
        
        <div class="content">
            <!-- Executive Summary -->
            <div class="summary">
                <div class="metric">
                    <div class="metric-value {{ 'success' if summary.overall_success else 'error' }}">
                        {{ "%.1f"|format(summary.success_rate) }}%
                    </div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.passed_sections }}/{{ summary.total_sections }}</div>
                    <div class="metric-label">Sections Passed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ "%.1f"|format(summary.total_duration_ms/1000) }}s</div>
                    <div class="metric-label">Total Duration</div>
                </div>
                <div class="metric">
                    <div class="metric-value {{ 'error' if summary.critical_failures > 0 else 'success' }}">
                        {{ summary.critical_failures }}
                    </div>
                    <div class="metric-label">Critical Failures</div>
                </div>
            </div>
            
            <!-- Test Sections -->
            {% for section in sections %}
            <div class="section">
                <div class="section-header">
                    <span>{{ section.name }}</span>
                    <span class="status-badge 
                        {% if section.critical and not section.success %}status-critical
                        {% elif section.success %}status-passed
                        {% else %}status-failed
                        {% endif %}">
                        {% if section.success %}✅ PASSED{% else %}❌ FAILED{% endif %}
                        {% if section.critical %}🚨{% endif %}
                    </span>
                </div>
                <div class="section-content">
                    <div class="details-grid">
                        <div class="detail-item">
                            <div class="detail-label">Duration</div>
                            <div class="detail-value">{{ "%.2f"|format(section.duration_ms) }}ms</div>
                        </div>
                        {% if 'test_summary' in section.details %}
                        <div class="detail-item">
                            <div class="detail-label">Test Summary</div>
                            <div class="detail-value">
                                {{ section.details.test_summary.total }} total, 
                                {{ section.details.test_summary.passed }} passed, 
                                {{ section.details.test_summary.failed }} failed
                            </div>
                        </div>
                        {% endif %}
                    </div>
                    {% if section.errors %}
                    <div style="margin-top: 15px;">
                        <strong>Errors:</strong>
                        <ul style="color: #dc3545; margin: 5px 0;">
                            {% for error in section.errors %}
                            <li>{{ error }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
            
            <!-- Recommendations -->
            {% if recommendations %}
            <div class="recommendations">
                <h3>📋 Recommendations</h3>
                <ul>
                    {% for rec in recommendations %}
                    <li>{{ rec }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}
            
            <!-- Environment Info -->
            <div class="section">
                <div class="section-header">
                    <span>🔧 Environment Information</span>
                </div>
                <div class="section-content">
                    <div class="details-grid">
                        <div class="detail-item">
                            <div class="detail-label">Python Version</div>
                            <div class="detail-value">{{ version_info.python_version.split()[0] }}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Platform</div>
                            <div class="detail-value">{{ version_info.platform }}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Ollama</div>
                            <div class="detail-value">{{ version_info.environment.ollama_base_url }}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Database</div>
                            <div class="detail-value">{{ version_info.environment.database_url }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        template = Template(template_str)
        return template.render(
            timestamp=report.timestamp,
            version_info=self.version_info,
            summary=report.summary,
            sections=report.sections,
            recommendations=report.recommendations
        )
    
    def _generate_simple_html_report(self, report: Phase7Report) -> str:
        """Generate simple HTML report without Jinja2"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>KRAI Phase 7 Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ color: green; }}
        .error {{ color: red; }}
        .warning {{ color: orange; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 KRAI Phase 7 Validation Report</h1>
        <p>Generated: {report.timestamp}</p>
        <p>Overall Status: {'✅ PASSED' if report.overall_success else '❌ FAILED'}</p>
        <p>Success Rate: {report.summary['success_rate']:.1f}%</p>
    </div>
    
    <h2>Test Sections</h2>
    """
        
        for section in report.sections:
            html += f"""
    <div class="section">
        <h3>{section.name} - {'✅ PASSED' if section.success else '❌ FAILED'}</h3>
        <p>Duration: {section.duration_ms:.2f}ms</p>"""
            
            if section.errors:
                html += f"""
        <p class="error">Errors: {', '.join(section.errors)}</p>"""
            
            html += """
    </div>
    """
        
        if report.recommendations:
            html += """
    <div class="section">
        <h2>📋 Recommendations</h2>
        <ul>
        """
            for rec in report.recommendations:
                html += f"        <li>{rec}</li>\n"
            html += """
        </ul>
    </div>
    """
        
        html += """
</body>
</html>
        """
        
        return html
    
    def display_console_summary(self, report: Phase7Report):
        """Display formatted console summary"""
        if not self.console:
            self._print_plain_summary(report)
            return
        
        # Summary panel
        summary_text = f"""
🧪 Phase 7 Validation Report
Generated: {report.timestamp}
Overall Status: {'✅ PASSED' if report.overall_success else '❌ FAILED'}

📊 Summary:
• Success Rate: {report.summary['success_rate']:.1f}%
• Sections: {report.summary['passed_sections']}/{report.summary['total_sections']} passed
• Critical Failures: {report.summary['critical_failures']}
• Duration: {report.summary['total_duration_ms']/1000:.1f}s
        """.strip()
        
        border_style = "green" if report.overall_success else "red"
        self.console.print(Panel(summary_text, title="📊 Phase 7 Validation Summary", border_style=border_style))
        
        # Sections table
        table = Table(title="Test Section Results", box=box.ROUNDED)
        table.add_column("Section", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Duration", style="yellow")
        table.add_column("Critical", style="red")
        
        for section in report.sections:
            status = "✅ PASSED" if section.success else "❌ FAILED"
            status_style = "green" if section.success else "red"
            critical = "🚨 Yes" if section.critical else "No"
            critical_style = "red" if section.critical and not section.success else "white"
            
            table.add_row(
                section.name,
                status,
                f"{section.duration_ms:.2f}ms",
                critical,
                style=status_style
            )
        
        self.console.print(table)
        
        # Recommendations
        if report.recommendations:
            self.console.print("\n📋 Recommendations:", style="yellow bold")
            for rec in report.recommendations:
                self.console.print(f"• {rec}", style="yellow")
    
    def _print_plain_summary(self, report: Phase7Report):
        """Print plain text summary"""
        print(f"\n🧪 Phase 7 Validation Report")
        print(f"Generated: {report.timestamp}")
        print(f"Overall Status: {'✅ PASSED' if report.overall_success else '❌ FAILED'}")
        print(f"Success Rate: {report.summary['success_rate']:.1f}%")
        print(f"Sections: {report.summary['passed_sections']}/{report.summary['total_sections']} passed")
        print(f"Critical Failures: {report.summary['critical_failures']}")
        print(f"Duration: {report.summary['total_duration_ms']/1000:.1f}s")
        
        print(f"\nTest Sections:")
        for section in report.sections:
            status = "✅ PASSED" if section.success else "❌ FAILED"
            critical = "🚨" if section.critical else ""
            print(f"  {section.name}: {status} {critical} ({section.duration_ms:.2f}ms)")
        
        if report.recommendations:
            print(f"\n📋 Recommendations:")
            for rec in report.recommendations:
                print(f"  • {rec}")
    
    async def generate_report(self) -> Phase7Report:
        """Generate complete Phase 7 validation report"""
        self.print_status("Generating Phase 7 validation report...", 'report')
        
        if not await self.setup():
            raise Exception("Setup failed")
        
        # Run all tests
        test_results = await self.run_all_tests()
        
        # Generate summary and recommendations
        summary = self.calculate_summary(test_results)
        recommendations = self.generate_recommendations(test_results)
        
        # Create report object
        report = Phase7Report(
            timestamp=self.version_info["timestamp"],
            environment=self.version_info["environment"],
            summary=summary,
            sections=test_results,
            recommendations=recommendations,
            overall_success=summary["overall_success"]
        )
        
        # Generate HTML report
        html_content = self.generate_html_report(report)
        html_path = self.output_dir / "phase7_report.html"
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        self.print_status(f"HTML report saved: {html_path}", 'success')
        
        # Generate JSON report
        json_path = self.output_dir / "phase7_report.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        self.print_status(f"JSON report saved: {json_path}", 'success')
        
        # Display console summary
        self.display_console_summary(report)
        
        return report
    
    async def run(self) -> int:
        """Main entry point"""
        try:
            report = await self.generate_report()
            
            # Return appropriate exit code
            if report.overall_success:
                self.print_status("🎉 Phase 7 validation completed successfully", 'success')
                return 0
            else:
                self.print_status("❌ Phase 7 validation completed with failures", 'error')
                return 1
                
        except Exception as e:
            self.print_status(f"Report generation failed: {e}", 'error')
            if self.verbose:
                self.print_status(f"Traceback: {traceback.format_exc()}", 'error')
            return 2

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate Phase 7 validation report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--output-dir", "-o", default="reports/phase7", help="Output directory for reports")
    
    args = parser.parse_args()
    
    generator = Phase7ReportGenerator(verbose=args.verbose, output_dir=args.output_dir)
    exit_code = await generator.run()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
