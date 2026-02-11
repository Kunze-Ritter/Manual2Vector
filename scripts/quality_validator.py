"""Quality validation module for production pipeline test runs."""

from typing import Any, Dict, List


class QualityValidator:
    def __init__(self, database_adapter, thresholds: Dict[str, Any]):
        self.database_adapter = database_adapter
        self.thresholds = thresholds

    async def validate(self, document_ids: List[str]) -> Dict[str, Any]:
        completeness = await self._check_completeness(document_ids)
        correctness = await self._check_correctness(document_ids)
        embeddings = await self._check_embeddings(document_ids)
        relationships = await self._check_relationships(document_ids)
        stage_status = await self._check_stage_status(document_ids)

        metrics = {
            "completeness": completeness,
            "correctness": correctness,
            "embeddings": embeddings,
            "relationships": relationships,
            "stage_status": stage_status,
        }

        overall_pass = all(metric.get("status") == "PASS" for metric in metrics.values())
        return {
            "status": "PASS" if overall_pass else "FAIL",
            "metrics": metrics,
        }

    async def _check_completeness(self, document_ids: List[str]) -> Dict[str, Any]:
        chunks_row = await self.database_adapter.fetch_one(
            "SELECT COUNT(*) as count FROM krai_intelligence.chunks WHERE document_id = ANY($1)",
            [document_ids],
        )
        images_row = await self.database_adapter.fetch_one(
            "SELECT COUNT(*) as count FROM krai_content.images WHERE document_id = ANY($1)",
            [document_ids],
        )
        error_codes_row = await self.database_adapter.fetch_one(
            "SELECT COUNT(*) as count FROM krai_intelligence.error_codes WHERE document_id = ANY($1)",
            [document_ids],
        )
        parts_row = await self.database_adapter.fetch_one(
            "SELECT COUNT(*) as count FROM krai_parts.parts_catalog WHERE document_id = ANY($1)",
            [document_ids],
        )

        chunks_count = self._row_value(chunks_row, "count")
        images_count = self._row_value(images_row, "count")
        error_codes_count = self._row_value(error_codes_row, "count")
        parts_count = self._row_value(parts_row, "count")

        chunk_pass = chunks_count >= self.thresholds.get("min_chunks", 100)
        image_pass = images_count >= self.thresholds.get("min_images", 10)
        error_code_pass = error_codes_count >= self.thresholds.get("min_error_codes", 5)
        parts_pass = parts_count >= self.thresholds.get("min_parts", 0)

        return {
            "chunks": {
                "count": chunks_count,
                "threshold": self.thresholds.get("min_chunks", 100),
                "status": "PASS" if chunk_pass else "FAIL",
            },
            "images": {
                "count": images_count,
                "threshold": self.thresholds.get("min_images", 10),
                "status": "PASS" if image_pass else "FAIL",
            },
            "error_codes": {
                "count": error_codes_count,
                "threshold": self.thresholds.get("min_error_codes", 5),
                "status": "PASS" if error_code_pass else "FAIL",
            },
            "parts": {
                "count": parts_count,
                "threshold": self.thresholds.get("min_parts", 0),
                "status": "PASS" if parts_pass else "FAIL",
            },
            "status": "PASS" if all([chunk_pass, image_pass, error_code_pass, parts_pass]) else "FAIL",
        }

    async def _check_correctness(self, document_ids: List[str]) -> Dict[str, Any]:
        rows = await self.database_adapter.fetch_all(
            """
            SELECT p.model_number, m.name as manufacturer
            FROM krai_core.products p
            JOIN krai_core.manufacturers m ON p.manufacturer_id = m.id
            WHERE p.document_id = ANY($1)
            """,
            [document_ids],
        )

        model_detected = False
        manufacturer_detected = False
        products_count = 0

        for row in rows or []:
            row_dict = dict(row)
            products_count += 1
            model_number = (row_dict.get("model_number") or "").lower()
            manufacturer = (row_dict.get("manufacturer") or "").lower()

            if "hp e877" in model_number or "e877" in model_number:
                model_detected = True
            if "hp inc." in manufacturer or manufacturer == "hp" or " hp " in f" {manufacturer} ":
                manufacturer_detected = True

        min_products = self.thresholds.get("min_products", 1)
        product_count_pass = products_count >= min_products
        correctness_pass = model_detected and manufacturer_detected and product_count_pass

        return {
            "products_count": products_count,
            "products_threshold": min_products,
            "model_detected": model_detected,
            "manufacturer_detected": manufacturer_detected,
            "status": "PASS" if correctness_pass else "FAIL",
        }

    async def _check_embeddings(self, document_ids: List[str]) -> Dict[str, Any]:
        total_chunks_row = await self.database_adapter.fetch_one(
            "SELECT COUNT(*) as count FROM krai_intelligence.chunks WHERE document_id = ANY($1)",
            [document_ids],
        )
        embedded_chunks_row = await self.database_adapter.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM krai_intelligence.chunks
            WHERE document_id = ANY($1) AND embedding IS NOT NULL
            """,
            [document_ids],
        )

        total_chunks = self._row_value(total_chunks_row, "count")
        chunks_with_embeddings = self._row_value(embedded_chunks_row, "count")
        coverage = (chunks_with_embeddings / total_chunks) if total_chunks > 0 else 0.0

        threshold = float(self.thresholds.get("min_embedding_coverage", 0.95))
        coverage_pass = coverage >= threshold

        return {
            "total_chunks": total_chunks,
            "chunks_with_embeddings": chunks_with_embeddings,
            "coverage": coverage,
            "threshold": threshold,
            "status": "PASS" if coverage_pass else "FAIL",
        }

    async def _check_relationships(self, document_ids: List[str]) -> Dict[str, Any]:
        row = await self.database_adapter.fetch_one(
            """
            SELECT
                COUNT(DISTINCT document_id) as doc_count,
                COUNT(DISTINCT id) as product_count
            FROM krai_core.products
            WHERE document_id = ANY($1)
            """,
            [document_ids],
        )

        doc_count = self._row_value(row, "doc_count")
        product_count = self._row_value(row, "product_count")
        relation_pass = product_count >= 1 and doc_count >= 1

        return {
            "linked_documents": doc_count,
            "linked_products": product_count,
            "status": "PASS" if relation_pass else "FAIL",
        }

    async def _check_stage_status(self, document_ids: List[str]) -> Dict[str, Any]:
        rows = await self.database_adapter.fetch_all(
            """
            SELECT document_id, stage_number, stage_name, status
            FROM krai_system.stage_tracking
            WHERE document_id = ANY($1)
            """,
            [document_ids],
        )

        total_records = len(rows or [])
        completed_stages = 0
        for row in rows or []:
            row_dict = dict(row)
            if row_dict.get("status") == "completed":
                completed_stages += 1

        expected_stage_records = len(document_ids) * 15
        stage_pass = total_records == expected_stage_records and completed_stages == expected_stage_records

        return {
            "total_stage_records": total_records,
            "expected_stage_records": expected_stage_records,
            "completed_stages": completed_stages,
            "expected_completed_stages": expected_stage_records,
            "status": "PASS" if stage_pass else "FAIL",
        }

    @staticmethod
    def _row_value(row: Any, key: str) -> int:
        if row is None:
            return 0
        row_dict = dict(row) if not isinstance(row, dict) else row
        return int(row_dict.get(key, 0))
