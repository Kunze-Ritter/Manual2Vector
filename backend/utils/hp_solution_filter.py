"""
HP Solution Filter
==================
Extracts technician-specific solutions from HP error codes
HP has 3 levels: customers, call-agents, onsite technicians
We only want the technician-level solution
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def extract_hp_technician_solution(solution_text: str) -> str:
    """
    Extract only technician-specific solution from HP error codes
    
    HP Format:
    - Recommended action for customers: (basic troubleshooting)
    - Recommended action for call-agents: (part replacement)
    - Recommended action for onsite technicians: (detailed repair)
    
    Args:
        solution_text: Full solution text with all 3 sections
        
    Returns:
        Technician-only solution or original text if not HP format
    """
    
    # Pattern to extract technician section
    technician_patterns = [
        # "Recommended action for onsite technicians:"
        r'Recommended\s+action\s+for\s+(?:onsite|service)\s+technicians?\s*[:]\s*'
        r'(.*?)'
        r'(?=Recommended\s+action|^\d+\.\d+\s+[A-Z]|\Z)',
        
        # "Service technician action:"
        r'Service\s+technician\s+action\s*[:]\s*'
        r'(.*?)'
        r'(?=Customer\s+action|Call\s+agent|^\d+\.\d+\s+[A-Z]|\Z)',
        
        # "Onsite technician:"
        r'Onsite\s+technician\s*[:]\s*'
        r'(.*?)'
        r'(?=Customer|Call\s+agent|^\d+\.\d+\s+[A-Z]|\Z)',
    ]
    
    for pattern in technician_patterns:
        match = re.search(pattern, solution_text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            technician_solution = match.group(1).strip()
            logger.debug(f"✅ Extracted HP technician-specific solution ({len(technician_solution)} chars)")
            
            # Clean up the solution
            cleaned = _clean_solution_text(technician_solution)
            return cleaned
    
    # Not HP format or no technician section found
    logger.debug("No HP technician section found, returning original solution")
    return solution_text


def _clean_solution_text(text: str) -> str:
    """
    Clean up solution text
    - Extract numbered steps
    - Remove extra whitespace
    - Limit to reasonable length
    """
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines[:30]:  # Max 30 lines for detailed technician steps
        line = line.strip()
        
        # Skip empty lines at start
        if not filtered_lines and not line:
            continue
        
        # Match steps: 1., 2., a), etc.
        if re.match(r'^(?:\d+[\.\)]|[a-z][\.\)]|•|-|\*)\s+', line):
            filtered_lines.append(line)
        # Continuation of previous step
        elif filtered_lines and len(line) > 20:
            filtered_lines[-1] += ' ' + line
        # Empty line between steps
        elif filtered_lines and not line:
            continue
        # Stop at new section header
        elif filtered_lines and re.match(r'^[A-Z][a-z]+\s+[A-Z]', line):
            break
    
    if filtered_lines:
        numbered_lines = []
        step_counter = 1
        for line in filtered_lines:
            stripped = line.lstrip()
            if re.match(r'^(\d+[\.\)]|[a-z][\.\)]|[-•*])\s+', stripped):
                numbered_lines.append(stripped)
                # Try to keep step counter in sync when explicit numbers exist
                number_match = re.match(r'^(\d+)[\.\)]', stripped)
                if number_match:
                    try:
                        step_counter = int(number_match.group(1)) + 1
                    except ValueError:
                        step_counter += 1
                else:
                    step_counter += 1
            else:
                numbered_lines.append(f"{step_counter}. {stripped}")
                step_counter += 1
        return '\n'.join(numbered_lines)

    # Fallback: return first 1000 chars
    return text[:1000].strip()


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
