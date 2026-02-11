"""Production test orchestrator for end-to-end pipeline validation."""

import asyncio
import glob
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from backend.core.base_processor import ProcessingContext, Stage
from backend.pipeline.master_pipeline import KRMasterPipeline
from scripts.quality_validator import QualityValidator
from scripts.report_generator import ReportGenerator


class ProductionTestOrchestrator:
    def __init__(
        self,
        pipeline: KRMasterPipeline,
        thresholds_path: str,
        threshold_overrides: Dict[str, Any],
        output_dir: Optional[str] = None,
        pdf_dir: Optional[str] = None,
        validate_dashboard: bool = False,
    ):
        self.console = Console()
        self.pipeline = pipeline
        self.thresholds = self._load_thresholds(thresholds_path, threshold_overrides)
        self.output_dir = self._detect_output_dir(output_dir)
        self.pdf_paths = self._detect_pdf_paths(pdf_dir)
        self.validate_dashboard = validate_dashboard
        self.test_run_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.document_ids: List[str] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    async def run(self) -> int:
        try:
            self.start_time = datetime.now()
            self._validate_environment()
            await self._cleanup_test_data()

            document_ids = await self._process_documents()
            if not document_ids:
                return 1

            quality_results = await self._validate_quality(document_ids)
            dashboard_results = await self._run_dashboard_validation(document_ids)
            self.end_time = datetime.now()

            report_path = self._generate_report(quality_results, dashboard_results)
            self.console.print(f"[green]Report generated:[/green] {report_path}")

            quality_failed = quality_results.get("status") != "PASS"
            dashboard_failed = (
                self.validate_dashboard
                and dashboard_results is not None
                and dashboard_results.get("status") == "FAIL"
            )

            return 1 if (quality_failed or dashboard_failed) else 0
        except Exception as error:
            self.end_time = datetime.now()
            self._generate_error_report(
                error,
                context={
                    "test_run_id": self.test_run_id,
                    "document_ids": self.document_ids,
                    "pdf_paths": self.pdf_paths,
                },
            )
            return 1

    def _validate_environment(self):
        upload_images_to_storage = os.getenv("UPLOAD_IMAGES_TO_STORAGE", "").lower()
        if upload_images_to_storage != "true":
            raise RuntimeError(
                "UPLOAD_IMAGES_TO_STORAGE must be set to 'true' for production test (MinIO required)."
            )

        r2_vars = ["R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"]
        if any(os.getenv(var) for var in r2_vars):
            raise RuntimeError(
                "R2 environment variables detected. Remove R2 configuration before running production test."
            )

        self.console.print("[green]Environment validation passed.[/green]")

    def _load_thresholds(self, thresholds_path: str, overrides: Dict[str, Any]) -> Dict[str, Any]:
        defaults = {
            "min_chunks": 100,
            "min_images": 10,
            "min_error_codes": 5,
            "min_embedding_coverage": 0.95,
            "min_products": 1,
            "min_parts": 0,
        }

        loaded = {}
        try:
            with open(thresholds_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
        except FileNotFoundError:
            loaded = defaults.copy()

        merged = defaults.copy()
        merged.update(loaded)
        merged.update(overrides or {})
        return merged

    def _detect_output_dir(self, output_dir: Optional[str]) -> str:
        if output_dir:
            target = Path(output_dir)
        elif os.getenv("GITHUB_WORKSPACE"):
            target = Path(os.getenv("GITHUB_WORKSPACE"))
        else:
            target = Path("./test_results/")

        target.mkdir(parents=True, exist_ok=True)
        return str(target.resolve())

    def _detect_pdf_paths(self, pdf_dir: Optional[str]) -> List[str]:
        matches: List[str] = []

        if pdf_dir:
            matches = glob.glob(os.path.join(pdf_dir, "HP*.pdf"))
            matches.extend(glob.glob(os.path.join(pdf_dir, "HP", "*.pdf")))
        else:
            windows_patterns = [
                r"C:\Firmwares\HP*.pdf",
                r"C:\Firmwares\HP\*.pdf",
            ]
            container_patterns = [
                "/firmwares/HP*.pdf",
                "/firmwares/HP/*.pdf",
            ]

            windows_matches: List[str] = []
            for pattern in windows_patterns:
                windows_matches.extend(glob.glob(pattern))

            container_matches: List[str] = []
            for pattern in container_patterns:
                container_matches.extend(glob.glob(pattern))

            matches = windows_matches if windows_matches else container_matches

        matches = sorted(set(matches))
        if not matches:
            raise RuntimeError("No HP PDF files found for production test.")

        if len(matches) < 2:
            raise RuntimeError("Production test requires 2 PDF files (HP_E877_SM.pdf and HP_E877_CPMD.pdf).")

        preferred = [
            path for path in matches
            if Path(path).name in ("HP_E877_SM.pdf", "HP_E877_CPMD.pdf")
        ]

        if len(preferred) == 2:
            return preferred
        return matches[:2]

    async def _is_safe_cleanup_target(self) -> bool:
        force_cleanup = os.getenv("PRODUCTION_TEST_FORCE_CLEANUP", "").lower() in ("1", "true", "yes")
        if force_cleanup:
            self.console.print(
                "[yellow]Cleanup safety bypassed with PRODUCTION_TEST_FORCE_CLEANUP.[/yellow]"
            )
            return True

        try:
            db_context = await self.pipeline.database_service.fetch_one(
                """
                SELECT
                    current_database() AS database_name,
                    current_schema() AS schema_name,
                    current_setting('search_path') AS search_path
                """
            )
        except Exception as error:
            self.console.print(
                f"[yellow]Cleanup safety warning:[/yellow] unable to read DB context ({error}); skipping cleanup."
            )
            return False

        context = dict(db_context) if db_context else {}
        context_values = [
            str(context.get("database_name") or "").lower(),
            str(context.get("schema_name") or "").lower(),
            str(context.get("search_path") or "").lower(),
        ]
        return any("krai_test" in value for value in context_values)

    async def _cleanup_test_data(self):
        try:
            if not await self._is_safe_cleanup_target():
                self.console.print(
                    "[yellow]Cleanup skipped:[/yellow] active database context is not a krai_test target."
                )
                return

            existing_rows = await self.pipeline.database_service.fetch_all(
                "SELECT id FROM krai_core.documents WHERE filename LIKE 'HP_E877%'"
            )
            document_ids = [str(dict(row).get("id")) for row in (existing_rows or [])]

            if not document_ids:
                self.console.print("[yellow]Cleanup: no existing HP_E877 test documents found.[/yellow]")
                return

            chunks_row = await self.pipeline.database_service.fetch_one(
                "SELECT COUNT(*) AS count FROM krai_intelligence.chunks WHERE document_id = ANY($1)",
                [document_ids],
            )
            images_row = await self.pipeline.database_service.fetch_one(
                "SELECT COUNT(*) AS count FROM krai_content.images WHERE document_id = ANY($1)",
                [document_ids],
            )

            deleted_docs = 0
            for document_id in document_ids:
                deleted = await self.pipeline.database_service.delete_document(document_id)
                if deleted:
                    deleted_docs += 1

            chunks_count = int(dict(chunks_row).get("count", 0)) if chunks_row else 0
            images_count = int(dict(images_row).get("count", 0)) if images_row else 0

            self.console.print(
                f"[green]Cleanup complete:[/green] documents={deleted_docs}, chunks={chunks_count}, images={images_count}"
            )
        except Exception as error:
            self.console.print(f"[yellow]Cleanup warning:[/yellow] {error}")

    async def _process_documents(self) -> List[str]:
        stages = list(Stage)
        total_steps = len(self.pdf_paths) * len(stages)
        document_ids: List[str] = []

        progress = Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console,
        )

        with progress as progress_instance:
            task_id = progress_instance.add_task("[cyan]Starting production test", total=total_steps)

            for pdf_path in self.pdf_paths:
                pdf_name = Path(pdf_path).name

                upload_processor = self.pipeline.processors.get("upload")
                if upload_processor is None:
                    self._generate_error_report(
                        RuntimeError("Upload processor not available."),
                        context={"pdf_path": pdf_path, "stage": Stage.UPLOAD.value},
                    )
                    return []

                progress_instance.update(
                    task_id,
                    description=f"[cyan]Processing {pdf_name} - Stage 1/15: {Stage.UPLOAD.value}",
                )

                upload_context = ProcessingContext(
                    document_id=str(uuid4()),
                    file_path=pdf_path,
                    document_type="service_manual",
                )
                upload_result = await upload_processor.process(upload_context)
                if not upload_result.success:
                    self._generate_error_report(
                        RuntimeError(str(upload_result.error) if upload_result.error else "Upload stage failed."),
                        context={"pdf_path": pdf_path, "stage": Stage.UPLOAD.value},
                    )
                    return []

                upload_data = upload_result.data or {}
                document_id = upload_data.get("document_id")
                if not document_id:
                    self._generate_error_report(
                        RuntimeError("Upload did not return a document_id."),
                        context={"pdf_path": pdf_path, "stage": Stage.UPLOAD.value},
                    )
                    return []

                await self.pipeline.track_stage_status(
                    document_id=str(document_id),
                    stage=Stage.UPLOAD,
                    status="running",
                    metadata={"pdf_path": pdf_path, "processor": "upload"},
                )

                await self.pipeline.track_stage_status(
                    document_id=str(document_id),
                    stage=Stage.UPLOAD,
                    status="completed",
                    metadata={"pdf_path": pdf_path, "processor": "upload"},
                )

                document_ids.append(str(document_id))
                self.document_ids = document_ids
                progress_instance.update(task_id, advance=1)

                for stage_index, stage in enumerate(stages[1:], start=2):
                    progress_instance.update(
                        task_id,
                        description=f"[cyan]Processing {pdf_name} - Stage {stage_index}/15: {stage.value}",
                    )

                    stage_result = await self.pipeline.run_single_stage(str(document_id), stage)
                    if not stage_result.get("success"):
                        self._generate_error_report(
                            RuntimeError(stage_result.get("error", "Stage failed.")),
                            context={
                                "document_id": str(document_id),
                                "stage": stage.value,
                                "pdf_path": pdf_path,
                            },
                        )
                        return []

                    progress_instance.update(task_id, advance=1)

        return document_ids

    async def _validate_quality(self, document_ids: List[str]) -> Dict[str, Any]:
        validator = QualityValidator(self.pipeline.database_service, self.thresholds)
        return await validator.validate(document_ids)

    @staticmethod
    def _is_ci_environment() -> bool:
        ci_vars = ["GITHUB_ACTIONS", "CI", "GITHUB_WORKSPACE"]
        return any(bool(os.getenv(var)) for var in ci_vars)

    async def _run_dashboard_validation(self, document_ids: List[str]) -> Optional[Dict[str, Any]]:
        if not self.validate_dashboard:
            return None

        if self._is_ci_environment():
            return {
                "status": "PENDING",
                "message": "Dashboard validation runs in separate CI step",
            }

        from tests.e2e.dashboard_production_test import DashboardValidator

        validator = DashboardValidator(
            base_url=os.getenv("DASHBOARD_URL", "http://localhost:8080"),
            document_ids=document_ids,
            output_dir=self.output_dir,
        )
        return await validator.validate()

    def _generate_report(
        self,
        quality_results: Dict[str, Any],
        dashboard_results: Optional[Dict[str, Any]] = None,
    ) -> str:
        generator = ReportGenerator(self.output_dir)
        test_results = {
            "test_run_id": self.test_run_id,
            "started_at": self.start_time.isoformat() if self.start_time else None,
            "ended_at": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self._duration_seconds(),
            "document_ids": self.document_ids,
            "pdf_paths": self.pdf_paths,
            "quality_results": quality_results,
            "dashboard_results": dashboard_results,
            "errors": [],
        }
        return generator.generate(test_results)

    def _generate_error_report(self, error: Exception, context: Dict[str, Any] = None):
        generator = ReportGenerator(self.output_dir)
        error_path = generator._generate_error_report(error, context or {})
        self.console.print(f"[red]Error report generated:[/red] {error_path}")

    def _duration_seconds(self) -> float:
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()
