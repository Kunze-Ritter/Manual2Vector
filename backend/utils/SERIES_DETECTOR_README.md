# Series Detector - Context-Aware Pattern Recognition

## Overview

The Series Detector identifies product series from model numbers with optional context validation to prevent false positives.

## Key Features

### 1. **Context-Aware Detection**
- Optional `context` parameter for validation
- Calculates confidence scores based on series name presence in context
- Rejects low-confidence matches for ambiguous patterns

### 2. **Manufacturer-Specific Patterns**

#### **Konica Minolta**
- **AccurioPrint** (Production): C659, C759, C2060, C2070, C4065
- **AccurioPress** (High-end Production): C1060, C3070, C4070, C4080, C6100, C7090, 6136P, etc.
- **bizhub Press** (Production): C1000, C1070, C1085, C1100, C3080, 1052, 1250, etc.
- **bizhub** (Office/MFP): C454e, C554e, C654e, 223, 227, 308, 454e, etc.
- **BIG Kiss** (Special): BIG Kiss, BIG Kiss II, BIG Kiss Plus

#### **HP**
- **LaserJet**: M479, M454, E50045, etc.
- **LaserJet Pro**: M15, M28, M29, etc.
- **OfficeJet Pro**: X580, X585, etc.
- **PageWide**: P77960, P55250, etc.
- **Color LaserJet**: CP5225, CP4525, etc.

#### **Canon**
- **imageRUNNER ADVANCE**: C5560i, C5550i, etc.
- **imageRUNNER**: iR2530, iR2545, etc.

## Usage

### Basic Usage (without context)
```python
from utils.series_detector import detect_series

result = detect_series('C4080', 'Konica Minolta')
# Returns: {'series_name': 'AccurioPress', 'model_pattern': 'Cxxxx', ...}
```

### Context-Aware Usage (recommended)
```python
from utils.series_detector import detect_series

# With context validation
context = "The AccurioPress C4080 is a high-end production printer..."
result = detect_series('C4080', 'Konica Minolta', context=context)
# Returns: {'series_name': 'AccurioPress', 'confidence': 1.0, ...}

# Short model number without context - REJECTED
result = detect_series('36', 'Konica Minolta')
# Returns: None

# Short model number with valid context - ACCEPTED
context = "The bizhub 36 is a compact multifunction printer"
result = detect_series('36', 'Konica Minolta', context=context)
# Returns: None (still rejected - no suffix, low confidence)

# Short model number with suffix and context - ACCEPTED
context = "The bizhub 20P specifications"
result = detect_series('20P', 'Konica Minolta', context=context)
# Returns: {'series_name': 'bizhub', 'confidence': 1.0, ...}
```

## Confidence Scoring

Confidence is calculated based on:
1. **Base confidence**: 0.5
2. **Series name in context**: +0.3
3. **Partial keyword match**: +0.1 per keyword
4. **Series marker match**: +0.2 (e.g., "AccurioPress", "bizhub", "LaserJet")

### Confidence Thresholds
- **Short model numbers (≤3 chars)**: Requires ≥0.7 confidence
- **Context-required patterns**: Requires ≥0.7 confidence
- **Longer model numbers**: No minimum threshold

## Pattern Priority (Konica Minolta)

Patterns are checked in this order to avoid false matches:

1. **BIG Kiss** (special naming)
2. **AccurioPrint** (specific models: C659, C759, C2060, C2070, C4065)
3. **AccurioPress** (high-end production: C4070, C4080, C6100, etc.)
4. **bizhub Press** (production: C1000, C1070, 1052, 1250, etc.)
5. **bizhub** (office/MFP: C454e, C554e, 223, 308, etc.)

## False Positive Prevention

### Short Model Numbers
- Model numbers ≤2 chars without context are **rejected**
- Model numbers ≤3 chars require **context validation**
- 2-digit bizhub models (20, 36, 42) require **suffix** (P, E, PX)

### Context Validation
- Patterns marked with `requires_context: True` **must** have context
- Low confidence matches are rejected
- Generic numbers (e.g., "42" in random text) are filtered out

## Return Value

```python
{
    'series_name': str,          # Marketing name (e.g., "AccurioPress")
    'model_pattern': str,        # Technical pattern (e.g., "Cxxxx")
    'series_description': str,   # Full description
    'confidence': float,         # 0.0-1.0 (only if context provided)
    'requires_context': bool     # True if pattern needs context validation
}
```

## Examples

### ✅ Correct Detections
```python
detect_series('C4080', 'Konica Minolta')  # AccurioPress
detect_series('C4065', 'Konica Minolta')  # AccurioPrint (not AccurioPress!)
detect_series('C659', 'Konica Minolta')   # AccurioPrint
detect_series('C454e', 'Konica Minolta')  # bizhub
detect_series('M479fdw', 'HP')            # LaserJet
```

### ❌ Rejected (False Positives)
```python
detect_series('36', 'Konica Minolta')     # Too short, no context
detect_series('42', 'Konica Minolta')     # Too short, no context
detect_series('20', 'Konica Minolta')     # Too short, no suffix
```

### ✅ Context-Validated
```python
context = "bizhub 20P specifications"
detect_series('20P', 'Konica Minolta', context)  # bizhub (confidence: 1.0)

context = "AccurioPress C4080 manual"
detect_series('C4080', 'Konica Minolta', context)  # AccurioPress (confidence: 1.0)
```

## Integration with Processors

When calling from processors, **always provide context** when available:

```python
# In series_processor.py or similar
from utils.series_detector import detect_series

# Get document chunk or product description as context
chunk_text = chunk.get('text', '')
product_description = product.get('description', '')
context = chunk_text or product_description

# Detect with context
series_data = detect_series(
    model_number=model_number,
    manufacturer_name=manufacturer_name,
    context=context  # ← Important!
)
```

## Testing

Run comprehensive tests:
```bash
python backend/utils/series_detector.py
```

## Notes

- **Priority matters**: AccurioPrint is checked before AccurioPress to avoid C4065 being misclassified
- **Context is optional but recommended**: Prevents false positives from generic numbers
- **Confidence scores**: Only calculated when context is provided
- **Short patterns**: Require suffixes or context validation to avoid false matches
