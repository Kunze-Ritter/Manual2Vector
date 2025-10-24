# TODO: Product Accessories & Options System

## Current Status: Phase 1 & 2 Complete! ✅🎉

- ✅ `product_accessories` junction table created (M:N) - Migration 72
- ✅ Database schema supports accessories
- ✅ Manual linking possible via SQL
- ✅ **Accessory Detection implemented!** (Phase 1.1) - `backend/utils/accessory_detector.py`
  - ✅ Konica Minolta accessories (23 patterns: DF-, FS-, SD-, PF-, etc.)
  - ✅ Model number prefix detection
  - ✅ Product type mapping (finisher, feeder, toner, etc.)
  - ✅ Compatible series detection
  - ✅ 23/23 tests passing (100%)
- ✅ **Automatic linking implemented!** (Phase 1.2, 1.3) - 2025-10-22
  - ✅ `backend/processors/accessory_linker.py` (280 lines)
  - ✅ Integrated into `document_processor.py` (Step 2d)
  - ✅ Auto-links accessories to products during processing
- ✅ **Advanced Compatibility Rules implemented!** (Phase 2) - 2025-10-22
  - ✅ `option_dependencies` table (Migration 106)
  - ✅ Configuration validator (320 lines)
  - ✅ Supports requires, excludes, alternative relationships
- ❌ No UI/Dashboard yet (Phase 3)

**Last Updated:** 2025-10-22 (09:20)

---

## Phase 1: Automatic Detection & Linking

### ✅ 1.1 Accessory Detection (COMPLETE - 2025-10-09)
**Goal:** Automatically identify which products are accessories/options

**Detection Rules:**
- [x] Model number prefixes (FS-, PF-, HT-, SD-, etc.) ✅
- [x] Keywords in product name ("Finisher", "Tray", "Cabinet", "Feeder") ✅
- [ ] From parts catalog (accessories section) - TODO
- [x] Product type = 'accessory' or 'option' ✅

**Implementation:** ✅ COMPLETE
```python
# backend/utils/accessory_detector.py (554 lines)
def detect_konica_minolta_accessory(model_number: str) -> Optional[AccessoryMatch]:
    """Detect Konica Minolta accessories/options"""
    # 23 patterns implemented:
    # - DF-* (Document Feeder)
    # - FS-* (Finisher)
    # - SD-* (Saddle Stitch)
    # - PF-* (Paper Feeder)
    # - TN-* (Toner)
    # - DR-* (Drum)
    # - etc.
```

**Documentation:** `backend/utils/ACCESSORY_DETECTION.md`

### ✅ 1.2 Compatibility Extraction (COMPLETE - 2025-10-22)
**Goal:** Extract which accessories fit which products

**Status:** ✅ Implemented!

**Implementation:**
```python
# backend/processors/accessory_linker.py (280 lines)
class AccessoryLinker:
    def link_accessories_for_document(document_id: UUID):
        """
        After document processing:
        1. Get all products from document
        2. Separate main products from accessories (use accessory_detector.py)
        3. Link accessories to main products
        4. Save to product_accessories table
        """
```

**Strategy Implemented:**
- ✅ Simple rule: If accessory mentioned in document → link to document's main products

**Features:**
- Automatic accessory detection via `_is_accessory()` method
- Uses product_type and accessory_detector patterns
- Supports 77 product types (finisher, feeder, toner, etc.)
- Comprehensive error handling and logging
- **Accessory Linker logging & validation** (07:45)
  - Added detailed logging for accessory/product linking steps
  - Detects invalid manufacturer/product combos before insert, preventing DB errors
  - **File:** `backend/processors/accessory_linker.py`
  - **Result:** Accessory linking step logs meaningful output and avoids invalid links
- **Accessory-Linker DNS Retry** (12:47)
  - Ergänzt `_execute_with_retry` für Supabase-Aufrufe (Lookup/Insert) mit Exponential Backoff
  - Fängt transienten `getaddrinfo failed` während Zubehörverknüpfung ab
  - **File:** `backend/processors/accessory_linker.py`
  - **Result:** Accessories linking bleibt stabil, auch wenn Supabase kurzzeitig nicht auflösbar ist

**File:** `backend/processors/accessory_linker.py` (280 lines)

### 1.3 Auto-Linking Integration (COMPLETE - 2025-10-22)
**Goal:** Integrate accessory linking into document processor

**Status:** 

**Implementation:**
- [x] Added to `document_processor.py` after product extraction 
- [x] New step: "Step 2d: Linking accessories to products" 
- [x] Runs after products are saved to DB 
- [x] Added to `document_processor.py` after product extraction ✅
- [x] New step: "Step 2d: Linking accessories to products" ✅
- [x] Runs after products are saved to DB ✅

**Flow:**
```
Step 2: Extract products
  ↓
Step 2b: Series detection
  ↓
Step 2c: Extract parts
  ↓
Step 2d: Link accessories ✅ IMPLEMENTED!
  - Detect which products are accessories (use accessory_detector.py)
  - Link accessories to main products
  - Save to product_accessories table
  - Log statistics
```

**Logging Output:**
```
Step 2d/5: Linking accessories to products...
📦 Document abc-123: 2 main products, 3 accessories
✅ Linked 3 accessories to 2 products (6 new links)
```

**File:** `backend/processors/document_processor.py` (lines 552-576)

---

## Phase 2: Advanced Compatibility Rules

### ✅ 2.1 Option Dependencies (COMPLETE - 2025-10-22)
**Goal:** Model complex relationships between options

**Status:** ✅ Implemented!

**Use Cases:**
- ✅ **Mutual Exclusion:** If Option X installed → Option Y cannot be installed
- ✅ **Requirements:** Option X requires Option Y to be installed first
- ✅ **Alternatives:** Option X OR Option Y (typically choose one)

**Database Schema:**
```sql
CREATE TABLE krai_core.option_dependencies (
    id UUID PRIMARY KEY,
    option_id UUID,              -- The option
    depends_on_option_id UUID,   -- Required/excluded option
    dependency_type VARCHAR(20), -- 'requires', 'excludes', 'alternative'
    notes TEXT,
    CONSTRAINT no_self_dependency CHECK (option_id != depends_on_option_id),
    CONSTRAINT unique_option_dependency UNIQUE (option_id, depends_on_option_id, dependency_type)
);
```

**Features:**
- ✅ Three dependency types: requires, excludes, alternative
- ✅ Self-dependency prevention
- ✅ Unique constraint per option pair
- ✅ Indexed for fast lookups
- ✅ RLS enabled for security
- ✅ View: `vw_option_dependencies` with product details

**File:** `database/migrations/106_create_option_dependencies.sql`

### ✅ 2.2 Configuration Validation (COMPLETE - 2025-10-22)
**Goal:** Validate product configurations before saving

**Status:** ✅ Implemented!

**Implementation:**
```python
# backend/utils/configuration_validator.py (320 lines)
class ConfigurationValidator:
    def validate_configuration(product_id: UUID, accessory_ids: List[UUID]) -> ValidationResult:
        """
        Check if accessory combination is valid
        Returns ValidationResult with:
        - valid: bool
        - errors: ['❌ Option X requires Option Y (missing)']
        - warnings: ['ℹ️ Option X and Y are alternatives']
        - recommendations: ['💡 Consider adding Option Z (standard)']
        """
```

**Features:**
- ✅ Checks 'requires' dependencies (errors if missing)
- ✅ Checks 'excludes' dependencies (errors if conflict)
- ✅ Checks 'alternative' dependencies (warnings)
- ✅ Recommends standard accessories
- ✅ Helper: `get_compatible_accessories()` with dependency info
- ✅ Comprehensive error messages with product names

**File:** `backend/utils/configuration_validator.py` (320 lines)

---

## Phase 3: Dashboard & UI (Future)

### 3.1 Accessory Management Dashboard
**Features:**
- [ ] View all products and their accessories
- [ ] Drag & drop to link accessories to products
- [ ] Visual compatibility matrix
- [ ] Bulk operations (link accessory to multiple products)

**UI Mockup:**
```
┌─────────────────────────────────────────────────┐
│ Product: bizhub C558                            │
├─────────────────────────────────────────────────┤
│ Compatible Accessories:                         │
│  ✓ Finisher FS-533          [Standard] [Remove]│
│  ✓ Paper Tray PF-707        [Optional] [Remove]│
│  + Add Accessory...                             │
└─────────────────────────────────────────────────┘
```

### 3.2 Dependency Rules Editor
**Features:**
- [ ] Define option dependencies visually
- [ ] Set mutual exclusions
- [ ] Define requirement chains
- [ ] Test configurations

**UI Mockup:**
```
┌─────────────────────────────────────────────────┐
│ Option: Finisher FS-533                         │
├─────────────────────────────────────────────────┤
│ Dependencies:                                   │
│  → Requires: Paper Tray PF-707                  │
│  ✗ Excludes: Compact Finisher FS-534            │
│  + Add Rule...                                  │
└─────────────────────────────────────────────────┘
```

### 3.3 Configuration Builder
**Features:**
- [ ] Select base product
- [ ] Add accessories with validation
- [ ] See price calculation
- [ ] Export configuration (PDF, JSON)

**UI Mockup:**
```
┌─────────────────────────────────────────────────┐
│ Configure: bizhub C558                          │
├─────────────────────────────────────────────────┤
│                                                 │
│ Selected Options:                               │
│  ✓ Finisher FS-533                              │
│  ✓ Paper Tray PF-707                            │
│  ⚠️ Large Capacity Tray      Incompatible!      │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## Implementation Priority

### ✅ **Completed:**
1. ✅ Database schema (Migration 72) - 2025-10-10
2. ✅ Accessory detection (Phase 1.1) - 2025-10-09
3. ✅ Konica Minolta patterns (23 types) - 2025-10-09
4. ✅ Compatibility extraction (Phase 1.2) - 2025-10-22
5. ✅ Auto-linking integration (Phase 1.3) - 2025-10-22
6. ✅ Option dependencies table (Migration 106) - 2025-10-22
7. ✅ Configuration validator (Phase 2.1, 2.2) - 2025-10-22

**🎉 PHASE 1 & 2 COMPLETE! All automatic detection, linking & validation implemented!**

### 🔥 **Now (High Priority):**
1. Apply Migration 106 to Supabase
2. Test the complete system:
   - Process a document with accessories
   - Verify links in product_accessories table
   - Test configuration validation
   - Add sample option dependencies

### 📅 **Later (Medium Priority):**
1. Advanced compatibility extraction
   - Parse compatibility tables from PDFs
   - Extract from parts catalogs
   - Auto-populate option_dependencies

### 🌟 **Future (Nice to Have):**
1. Dashboard UI (Phase 3)
2. Configuration builder
3. Visual dependency editor
4. Multi-manufacturer support (HP, Canon, Xerox, etc.)

---

## Technical Notes

### Database Queries

**Get all accessories for a product:**
```sql
SELECT p.model_number, pa.is_standard
FROM product_accessories pa
JOIN products p ON p.id = pa.accessory_id
WHERE pa.product_id = 'c558-uuid';
```

**Get all products compatible with an accessory:**
```sql
SELECT p.model_number
FROM product_accessories pa
JOIN products p ON p.id = pa.product_id
WHERE pa.accessory_id = 'fs533-uuid';
```

**Find accessories mentioned in document:**
```sql
-- Get document's products
SELECT id FROM products WHERE id IN (
    SELECT product_id FROM document_products WHERE document_id = 'doc-uuid'
);

-- Get accessories mentioned in same document
SELECT DISTINCT p.id, p.model_number
FROM products p
JOIN document_products dp ON dp.product_id = p.id
WHERE dp.document_id = 'doc-uuid'
  AND is_accessory(p.model_number) = true;
```

---

## Related Files

- `database/migrations/72_remove_parent_id_add_accessories_junction.sql`
- `database/migrations/PRODUCT_ACCESSORIES_GUIDE.md`
- `backend/core/data_models.py` (ProductModel)
- `backend/processors/document_processor.py` (future: accessory linking)

---

## Questions to Answer

1. **Accessory Prefixes:** Complete list of prefixes (FS-, PF-, HT-, SD-, ...)
2. **Compatibility Sources:** Where is compatibility info most reliable?
3. **UI Framework:** What to use for dashboard? (React, Vue, Svelte?)
4. **Priority:** When to build dashboard vs improve extraction?

---

**Last Updated:** 2025-10-22 (09:20)  
**Status:** 🎉 Phase 1 & 2 COMPLETE! Ready for testing  
**Next Action:** Apply Migration 106, then test complete system

---

## Recent Updates

### 2025-10-22 (09:16-09:20) 🎉 PHASE 2 COMPLETE!
- ✅ **Implemented Phase 2.1:** Option Dependencies
  - Created Migration 106: `option_dependencies` table
  - Three dependency types: requires, excludes, alternative
  - Indexed for fast lookups, RLS enabled
  - View: `vw_option_dependencies` with product details
- ✅ **Implemented Phase 2.2:** Configuration Validation
  - Created `backend/utils/configuration_validator.py` (320 lines)
  - Validates configurations against dependencies
  - Returns errors, warnings, recommendations
  - Helper: `get_compatible_accessories()` with dependency info
- ✅ **Phase 2 is now 100% complete!**

### 2025-10-22 (09:11-09:15) 🎉 PHASE 1 COMPLETE!
- ✅ **Implemented Phase 1.2:** Compatibility Extraction
  - Created `backend/processors/accessory_linker.py` (280 lines)
  - Automatic accessory detection and linking
  - Statistics tracking and error handling
- ✅ **Implemented Phase 1.3:** Auto-Linking Integration
  - Integrated into `document_processor.py` (Step 2d)
  - Runs automatically during document processing
  - Comprehensive logging output
- ✅ **Phase 1 is now 100% complete!**

### 2025-10-22 (09:07)
- ✅ Updated status: Phase 1.1 is complete!
- ✅ Marked completed tasks with timestamps
- ✅ Updated priorities (Phase 1.2 is now HIGH priority)
- ✅ Added effort estimates and blockers

### 2025-10-09
- ✅ Implemented `accessory_detector.py` (554 lines)
- ✅ 23 Konica Minolta accessory patterns
- ✅ 23/23 tests passing (100%)
- ✅ Documentation: `ACCESSORY_DETECTION.md`

### 2025-10-10
- ✅ Created `product_accessories` junction table (Migration 72)
- ✅ Database schema ready for M:N relationships
