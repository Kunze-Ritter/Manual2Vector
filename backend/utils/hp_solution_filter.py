"""
HP Solution Filter
==================
Extracts technician-specific solutions from HP error codes
HP has 3 levels: customers, call-agents, onsite technicians
We only want the technician-level solution
"""

import re
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Section header patterns for each level (case-insensitive, flexible spacing)
_CUSTOMER_HEADERS = [
    r'Recommended\s+action\s+for\s+customers?\b',
]
_AGENT_HEADERS = [
    r'Recommended\s+action\s+for\s+call[\-\s]center\s+agents?\b',
    r'Recommended\s+action\s+for\s+call[\-\s]agents?\b',
]
_TECHNICIAN_HEADERS = [
    r'Recommended\s+action\s+for\s+(?:onsite|on-site|service)\s+technicians?\b',
    r'Service\s+technician\s+action\b',
    r'Onsite\s+technician\b',
]
_COMBINED_AGENT_TECH_HEADERS = [
    r'Recommended\s+action\s+for\s+call[\-\s](?:center\s+)?agents?(?:\s*,\s*|\s+and\s+)(?:and\s+)?(?:onsite\s+)?technicians?\b',
]
_GENERIC_HEADER = r'Recommended\s+action\b'
_NEXT_CODE_STOP = re.compile(r'\n\d{2,3}\.\d{2}[\.\d]*\s+\S', re.MULTILINE)


def _find_section(text: str, header_patterns: list) -> Optional[str]:
    """Find the first matching section header and return text until next section."""
    flags = re.IGNORECASE | re.DOTALL
    for pat in header_patterns:
        m = re.search(pat, text, flags)
        if not m:
            continue
        start = m.end()
        # Require section stopper to begin on its own line to avoid matching
        # e.g. "onsite technicians" inside "agents and onsite technicians".
        next_section = re.search(
            r'(?:^|\n)\s*(?:Recommended\s+action|Service\s+technician\s+action|Onsite\s+technician)',
            text[start:], re.IGNORECASE | re.MULTILINE,
        )
        stop = next_section.start() if next_section else len(text[start:])
        code_stop = _NEXT_CODE_STOP.search(text[start: start + stop])
        if code_stop:
            stop = min(stop, code_stop.start())
        return text[start: start + stop].strip()
    return None


def extract_all_hp_levels(text: str) -> Dict[str, Optional[str]]:
    """
    Extract all three solution levels from an HP chunk/solution text.

    Returns a dict with keys:
        - 'customer'    : solution_customer_text  (Level 1 — basic steps)
        - 'agent'       : solution_agent_text      (Level 2 — call-center)
        - 'technician'  : solution_technician_text (Level 3 — on-site preferred)

    For non-HP or single-level text all keys except 'technician' will be None.
    """
    result: Dict[str, Optional[str]] = {'customer': None, 'agent': None, 'technician': None}
    if not text:
        return result

    # Check for combined "agents and technicians" header FIRST to avoid
    # partial matches of _AGENT_HEADERS, which stops at word boundary "agents"
    # and leaves " and onsite technicians" as a confusing prefix.
    combined = _find_section(text, _COMBINED_AGENT_TECH_HEADERS)
    if combined:
        agent_text = technician_text = combined
        customer_text = _find_section(text, _CUSTOMER_HEADERS)
    else:
        customer_text   = _find_section(text, _CUSTOMER_HEADERS)
        agent_text      = _find_section(text, _AGENT_HEADERS)
        technician_text = _find_section(text, _TECHNICIAN_HEADERS)

    if customer_text or agent_text or technician_text:
        result['customer']   = _clean_solution_text(customer_text)   if customer_text   else None
        result['agent']      = _clean_solution_text(agent_text)      if agent_text      else None
        result['technician'] = _clean_solution_text(technician_text) if technician_text else None
        return result

    # No level headers — try generic "Recommended action"
    generic = _find_section(text, [_GENERIC_HEADER])
    if generic:
        result['technician'] = _clean_solution_text(generic)
        return result

    # Last fallback: full text as technician level
    result['technician'] = _clean_solution_text(text)
    return result


def extract_hp_technician_solution(solution_text: str) -> str:
    """
    Backward-compatible wrapper — extract only the technician-level solution.
    Prefer extract_all_hp_levels() for new code.
    """
    levels = extract_all_hp_levels(solution_text)
    return levels['technician'] or levels['agent'] or levels['customer'] or solution_text


def _clean_solution_text(text: Optional[str]) -> Optional[str]:
    """
    Clean up solution text: normalize whitespace and remove leading/trailing
    blank lines.  Returns None if input is None or empty.

    We deliberately do NOT truncate — the caller stores the full extracted
    section so that the chat response can show every step and note that
    appears in the service manual.
    """
    if not text or not text.strip():
        return None
    # Collapse runs of blank lines to a single blank line
    cleaned = re.sub(r'\n{3,}', '\n\n', text)
    return cleaned.strip()


def is_hp_multi_level_format(text: str) -> bool:
    """
    Check if text contains HP multi-level format
    (customers, call-agents, technicians)
    
    Returns:
        True if HP multi-level format detected
    """
    indicators = [
        r'Recommended\s+action\s+for\s+customers',
        r'Recommended\s+action\s+for\s+call-agents',
        r'Recommended\s+action\s+for\s+(?:onsite|service)\s+technicians',
    ]
    
    matches = sum(1 for pattern in indicators if re.search(pattern, text, re.IGNORECASE))
    
    # If we find at least 2 of the 3 sections, it's HP format
    return matches >= 2
