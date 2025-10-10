# TODO: Product Accessories & Options System

## Current Status: Basic Infrastructure ✅

- ✅ `product_accessories` junction table created (M:N)
- ✅ Database schema supports accessories
- ✅ Manual linking possible via SQL
- ❌ No automatic detection/linking yet
- ❌ No UI/Dashboard yet

---

## Phase 1: Automatic Detection & Linking (Next Priority)

### 1.1 Accessory Detection
**Goal:** Automatically identify which products are accessories/options

**Detection Rules:**
- [ ] Model number prefixes (FS-, PF-, HT-, SD-, etc.)
- [ ] Keywords in product name ("Finisher", "Tray", "Cabinet", "Feeder")
- [ ] From parts catalog (accessories section)
- [ ] Product type = 'accessory' or 'option'

**Implementation:**
```python
# backend/utils/accessory_detector.py
def is_accessory(model_number: str, product_name: str = None) -> bool:
    """Detect if a product is an accessory"""
    # Check prefixes: FS-, PF-, HT-, SD-, etc.
    # Check keywords: Finisher, Tray, Cabinet, etc.
    pass
```

### 1.2 Compatibility Extraction
**Goal:** Extract which accessories fit which products

**Sources:**
- [ ] **Service Manual Text:** "Compatible with: C558, C658, C758"
- [ ] **Tables in PDF:** Compatibility matrices
- [ ] **Parts Catalog:** Accessory listings with compatible models
- [ ] **Product Configurations:** Option dependencies

**Extraction Strategy:**
```python
# If accessory mentioned in document → compatible with document's products
# Example: FS-533 mentioned in bizhub C558 manual → link them
```

**Implementation:**
```python
# backend/processors/accessory_linker.py
def link_accessories_to_products(document_id: UUID):
    """
    After document processing:
    1. Get all products from document
    2. Get all accessories mentioned in document
    3. Link accessories to main products
    """
    pass
```

### 1.3 Auto-Linking Integration
**Where to integrate:**
- [ ] In `document_processor.py` after product extraction
- [ ] New step: "Step 2d: Linking accessories to products"
- [ ] Run after products are saved to DB

**Flow:**
```
Step 2: Extract products
  ↓
Step 2b: Series detection
  ↓
Step 2c: Extract parts
  ↓
Step 2d: Link accessories (NEW!)
  - Detect which products are accessories
  - Link accessories to main products
  - Save to product_accessories table
```

---

## Phase 2: Advanced Compatibility Rules (Future)

### 2.1 Option Dependencies
**Goal:** Model complex relationships between options

**Use Cases:**
- ❌ **Mutual Exclusion:** If Option X installed → Option Y cannot be installed
- ✅ **Requirements:** Option X requires Option Y to be installed first
- 🔄 **Alternatives:** Option X OR Option Y (not both)

**Database Schema (Future):**
```sql
CREATE TABLE krai_core.option_dependencies (
    id UUID PRIMARY KEY,
    option_id UUID,              -- The option
    depends_on_option_id UUID,   -- Required option
    dependency_type VARCHAR(20), -- 'requires', 'excludes', 'alternative'
    notes TEXT
);
```

**Example:**
```sql
-- Finisher FS-533 requires Paper Tray PF-707
INSERT INTO option_dependencies (option_id, depends_on_option_id, dependency_type)
VALUES ('fs533-id', 'pf707-id', 'requires');

-- Large Capacity Tray excludes Standard Tray
INSERT INTO option_dependencies (option_id, depends_on_option_id, dependency_type)
VALUES ('lct-id', 'std-tray-id', 'excludes');
```

### 2.2 Configuration Validation
**Goal:** Validate product configurations before saving

```python
def validate_configuration(product_id: UUID, accessory_ids: List[UUID]) -> Dict:
    """
    Check if accessory combination is valid
    Returns: {
        'valid': bool,
        'errors': ['Option X excludes Option Y'],
        'warnings': ['Option X recommended with Option Y']
    }
    """
    pass
```

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
│ Base Price: $5,999                              │
│                                                 │
│ Selected Options:                               │
│  ✓ Finisher FS-533          +$1,200            │
│  ✓ Paper Tray PF-707        +$400              │
│  ⚠️ Large Capacity Tray      Incompatible!      │
│                                                 │
│ Total: $7,599                                   │
└─────────────────────────────────────────────────┘
```

---

## Implementation Priority

### 🔥 **Now (Critical):**
1. Fix series linking bug
2. Fix OCR/Vision AI data saving
3. Fix image-to-chunk linking

### 🎯 **Next (High Priority):**
1. Implement basic accessory detection (Phase 1.1)
2. Implement simple auto-linking (Phase 1.2, 1.3)
   - Rule: If accessory mentioned in document → link to document's products

### 📅 **Later (Medium Priority):**
1. Advanced compatibility extraction (Phase 2.1)
2. Option dependencies (Phase 2.2)

### 🌟 **Future (Nice to Have):**
1. Dashboard UI (Phase 3)
2. Configuration builder
3. Visual dependency editor

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

**Last Updated:** 2025-10-10  
**Status:** Planning Phase  
**Next Action:** Implement Phase 1.1 (Accessory Detection)
