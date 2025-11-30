# Legacy Regex Replacement - Action Items

## Problem Analysis
Current code has **crITICAL ISSUES** with hardcoded patterns:

1. **Product Extractor**: Uses outdated regex patterns instead of YAML configs
2. **Error Code Extractor**: Uses static JSON patterns, not synchronized with manufacturer configs  
3. **OEM Detection**: Inconsistent mapping between manufacturers
4. **Rejection Rules**: Hardcoded instead of config-driven

## Priority Tasks

### ✅ Phase 1: Complete OEM Detection System
- [ ] Test current `config/oem_mappings.py` implementation
- [ ] Add missing producer-to-OEM relationships (especially Ricoh/Brother)
- [ ] Enhance series-based OEM detection (e.g., "5000i" → Brother engine)
- [ ] Verify OEM usage in both extractors

### ✅ Phase 2: Generate Error Code Patterns from YAML
- [ ] Create `config/generate_error_code_patterns.py` (like producer patterns)
- [ ] Transform YAML configs to regex patterns for error extraction
- [ ] Test pattern generation for all manufacturers
- [ ] Replace static JSON with dynamic pattern loading

### ⚠️ Phase 3: Update Product Extractor
- [ ] Remove hardcoded regex patterns (HP_PATTERNS, CANON_PATTERNS, etc.)
- [ ] Force use of manufacturer YAML configs only
- [ ] Add error handling for missing configs
- [ ] Test with all manufacturer configurations

### ⚠️ Phase 4: Update Error Code Extractor  
- [ ] Remove static JSON patterns
- [ ] Load patterns from YAML-generated configs
- [ ] Ensure OEM manufacturer mapping works correctly
- [ ] Test enrichment with generated patterns

### ⚠️ Phase 5: Configuration Synchronization
- [ ] Create `sync_all_patterns.py` script
- [ ] Ensure producer and error code patterns stay in sync
- [ ] Add validation for missing manufacturers
- [ ] Test complete pipeline with mixed OEM cases

## Success Criteria
- ✅ **Zero hardcoded regex patterns**
- ✅ **All manufacturers use YAML configs**
- ✅ **Consistent OEM detection across extractors**
- ✅ **Complete test coverage for OEM cases**

## Current Status
- Manufacturer configs: ✅ Operational
- Producer pattern generation: ✅ Working
- OEM mappings: ⚠️ Partial (needs Ricoh/Brother testing)
- Error code pattern generation: ❌ Not implemented
- Legacy cleanup: ❌ Not started
