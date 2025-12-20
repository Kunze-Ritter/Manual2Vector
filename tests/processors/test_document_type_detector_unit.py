from typing import Dict, Any

import pytest

from backend.processors.document_type_detector import DocumentTypeDetector


pytestmark = [pytest.mark.unit, pytest.mark.classification]


def _make_detector() -> DocumentTypeDetector:
    return DocumentTypeDetector(debug=False)


class TestDocumentTypeDetection:
    @pytest.mark.parametrize(
        "title,filename,error_count,parts_count,expected",
        [
            ("Parts Guide", "canon_parts_catalog.pdf", 0, 10, "parts_catalog"),
            ("Service Manual", "hp_service_manual.pdf", 5, 0, "service_manual"),
            ("User Guide", "hp_user_guide.pdf", 0, 0, "user_manual"),
            ("Installation Guide", "setup_guide.pdf", 0, 0, "installation_guide"),
            ("Marketing Brochure", "brochure.pdf", 0, 0, "service_manual"),
        ],
    )
    def test_detect_type_variants(
        self,
        title: str,
        filename: str,
        error_count: int,
        parts_count: int,
        expected: str,
    ) -> None:
        det = _make_detector()
        result = det._detect_type(  # type: ignore[attr-defined]
            title=title.lower(),
            filename=filename.lower(),
            error_codes_count=error_count,
            parts_count=parts_count,
        )
        assert result == expected


class TestVersionDetection:
    @pytest.mark.parametrize(
        "title,filename,creation,manufacturer,doc_type,expected",
        [
            (
                "Konica Minolta Parts Catalog",
                "bizhub_c4080_parts.pdf",
                "D:20250808064126Z",
                "Konica Minolta",
                "parts_catalog",
                "August 2025",
            ),
            ("Manual v1.0", "hp_manual_v1.0.pdf", "", "HP", "service_manual", "1.0"),
            ("Service Manual Version 2.5", "sm.pdf", "", "Canon", "service_manual", "2.5"),
            ("Rev A Service Manual", "sm_rev_a.pdf", "", "Canon", "service_manual", "A"),
            ("Edition 3", "sm.pdf", "", "Canon", "service_manual", "3"),
        ],
    )
    def test_detect_version_patterns(
        self,
        title: str,
        filename: str,
        creation: str,
        manufacturer: str,
        doc_type: str,
        expected: str,
    ) -> None:
        det = _make_detector()
        version = det._detect_version(  # type: ignore[attr-defined]
            title=title.lower(),
            filename=filename.lower(),
            creation_date=creation,
            document_type=doc_type,
            manufacturer=manufacturer,
        )
        assert version == expected

    @pytest.mark.parametrize(
        "filename,expected",
        [
            ("A93E.pdf", "A93E"),
            ("ACET011.pdf", "ACET011"),
            ("no_code_here.pdf", None),
        ],
    )
    def test_detect_version_document_code(self, filename: str, expected: str | None) -> None:
        det = _make_detector()
        version = det._detect_version(  # type: ignore[attr-defined]
            title="",
            filename=filename.lower(),
            creation_date="",
            document_type="service_manual",
            manufacturer="Konica Minolta",
        )
        assert version == expected


class TestDateVersionExtraction:
    @pytest.mark.parametrize(
        "creation,expected",
        [
            ("D:20250808064126Z", "August 2025"),
            ("D:20250101000000", "January 2025"),
            ("", None),
            ("INVALID", None),
            ("D:20251301000000", None),
        ],
    )
    def test_extract_date_version(self, creation: str, expected: str | None) -> None:
        det = _make_detector()
        result = det._extract_date_version(creation)  # type: ignore[attr-defined]
        assert result == expected


class TestDetectIntegration:
    def test_detect_full_hp_service_manual(self) -> None:
        det = _make_detector()
        pdf_metadata: Dict[str, Any] = {
            "title": "HP LaserJet Service Manual v1.0",
            "filename": "hp_lj_sm_v1.0.pdf",
            "creation_date": "D:20240115000000Z",
        }
        stats = {"total_error_codes": 3, "parts_count": 0}

        doc_type, version = det.detect(pdf_metadata, stats, manufacturer="HP")
        assert doc_type == "service_manual"
        assert version in {"1.0", None}

    def test_detect_full_canon_parts_catalog(self) -> None:
        det = _make_detector()
        pdf_metadata: Dict[str, Any] = {
            "title": "Canon imageRUNNER C5560 Parts Catalog",
            "filename": "canon_ir_c5560_parts.pdf",
            "creation_date": "D:20240808064126Z",
        }
        stats = {"total_error_codes": 0, "parts_count": 100}

        doc_type, version = det.detect(pdf_metadata, stats, manufacturer="Canon")
        assert doc_type == "parts_catalog"
        assert version in {None, "August 2024"}

    def test_detect_with_empty_metadata(self) -> None:
        det = _make_detector()
        pdf_metadata: Dict[str, Any] = {}
        stats = {"total_error_codes": 0, "parts_count": 0}

        doc_type, version = det.detect(pdf_metadata, stats, manufacturer=None)
        assert doc_type == "service_manual"
        assert version is None
