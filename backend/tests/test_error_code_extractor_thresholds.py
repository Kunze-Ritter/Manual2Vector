import pytest
from backend.processors.error_code_extractor import ErrorCodeExtractor
from backend.processors.models import ExtractedErrorCode


def _make_code(solution_text: str) -> ExtractedErrorCode:
    return ExtractedErrorCode(
        error_code="13.B9.Az",
        error_description="Paper jam in fuser area detected",
        solution_technician_text=solution_text,
        context_text="Error code 13.B9.Az indicates a paper jam in the fuser area of the printer unit.",
        confidence=0.8,
        page_number=1,
        extraction_method="test",
    )


def test_enrichment_skips_codes_with_solution_over_500_chars_not_100():
    """Codes with 101-499 char solutions must still be enriched (Bug 4 fix)."""
    extractor = ErrorCodeExtractor()
    short_partial = "Fix the paper jam by opening the door. " * 3  # ~120 chars, partial
    code = _make_code(short_partial)
    needs_enrichment = [
        ec for ec in [code]
        if not ec.solution_technician_text or len(ec.solution_technician_text) <= 500
    ]
    assert len(needs_enrichment) == 1, "Code with <500 char solution must need enrichment"


def test_enrichment_skips_codes_with_solution_over_500_chars():
    """Codes with >500 char solutions can skip enrichment."""
    extractor = ErrorCodeExtractor()
    long_solution = "Step 1: Open front cover. Step 2: Remove jam. Step 3: Check sensor. " * 10  # >500 chars
    code = _make_code(long_solution)
    needs_enrichment = [
        ec for ec in [code]
        if not ec.solution_technician_text or len(ec.solution_technician_text) <= 500
    ]
    assert len(needs_enrichment) == 0, "Code with >500 char solution should skip enrichment"


def test_early_exit_threshold_is_1500_not_200():
    """The early-exit threshold in the enrichment match loop must be >1500, not >200 (Bug 1 fix)."""
    import inspect
    from backend.processors import error_code_extractor as ece_module
    source = inspect.getsource(ece_module.ErrorCodeExtractor.enrich_error_codes_from_document)
    # The old (wrong) threshold was > 200 — ensure it is NOT present and > 1500 IS present
    assert '> 200' not in source, "Old threshold '> 200' still present in enrich_error_codes"
    assert '> 1500' in source, "New threshold '> 1500' not found in enrich_error_codes"


def test_extract_description_allows_up_to_1500_chars(tmp_path):
    """_extract_description max_length must be 1500, not 500 (Bug 2 fix)."""
    extractor = ErrorCodeExtractor()
    long_desc = "Classification: " + ("This is a detailed error description. " * 50)  # >500 chars
    result = extractor._extract_description(long_desc, 0, max_length=1500)
    if result:
        assert not result.endswith("..."), "Description must not be truncated with ellipsis"
        assert len(result) <= 1500


def test_bullet_line_cap_is_30_not_8():
    """Bullet line cap in _extract_solution must be [:30] not [:8] (Bug 3 fix)."""
    import inspect
    from backend.processors import error_code_extractor as ece_module
    source = inspect.getsource(ece_module.ErrorCodeExtractor._extract_solution)
    # Verify the cap was raised from 8 to 30
    assert '[:8]' not in source, "Old bullet cap '[:8]' still present in _extract_solution"
    assert '[:30]' in source, "New bullet cap '[:30]' not found in _extract_solution"
