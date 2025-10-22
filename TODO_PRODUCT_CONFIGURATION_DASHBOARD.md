# TODO: Product Configuration Dashboard

## Current Status: Phase 1 & 2 Complete, Phase 3 Ready to Build! 🚀

**Last Updated:** 2025-10-22 (10:15)

---

## 🎯 Vision

Ein interaktives Dashboard zum:
1. **Verwalten** von Product Dependencies (requires, excludes, alternatives)
2. **Konfigurieren** von Produkten mit Accessories/Options
3. **Validieren** von Konfigurationen (Konflikte erkennen)
4. **Visualisieren** von Kompatibilitäten und Abhängigkeiten

---

## ✅ Was bereits existiert (Backend)

### Database Schema
- ✅ `product_accessories` table (M:N) - Links products to accessories
- ✅ `option_dependencies` table - Models requires/excludes/alternative relationships
- ✅ 12 neue product_types (finisher_accessory, controller_accessory, image_controller, etc.)

### Backend Logic
- ✅ `accessory_linker.py` (280 lines) - Auto-links accessories during processing
- ✅ `configuration_validator.py` (320 lines) - Validates configurations
- ✅ `accessory_detector.py` (456 lines) - Detects 30+ accessory types
- ✅ `product_type_mapper.py` - Maps 200+ series to product types

### Sample Data
- ✅ 4 Dependencies in DB (PK-524, PK-526 → FS-533, FS-534)
- ✅ Migration 108 ready for more dependencies

---

## 📋 Phase 3: Dashboard & UI

### 3.1 Product Configuration Builder ⭐ HIGH PRIORITY

**Goal:** Interactive UI to configure a product with accessories

**Features:**
- [ ] **Product Selection**
  - Select base product (e.g., bizhub C558)
  - Show compatible accessories (from `product_accessories` table)
  
- [ ] **Accessory Selection**
  - Drag & drop accessories to configuration
  - Visual indicators: ✅ compatible, ⚠️ requires, ❌ conflicts
  - Real-time validation using `configuration_validator.py`
  
- [ ] **Validation Display**
  - Show errors: "❌ PK-524 requires FS-533 (missing)"
  - Show warnings: "ℹ️ FS-533 and FS-534 are alternatives"
  - Show recommendations: "💡 Consider adding RU-513 (required for FS-534)"
  
- [ ] **Configuration Summary**
  - List all selected accessories
  - Total price (if available)
  - Export as PDF/JSON

**API Endpoints needed:**
```python
# GET /api/products/{product_id}/compatible-accessories
# Returns: List of compatible accessories with dependency info

# POST /api/products/{product_id}/validate-configuration
# Body: { "accessory_ids": ["id1", "id2"] }
# Returns: ValidationResult (valid, errors, warnings, recommendations)

# POST /api/products/{product_id}/save-configuration
# Body: { "name": "My Config", "accessory_ids": [...] }
# Returns: Configuration ID
```

**UI Framework:** React + TailwindCSS + shadcn/ui
**Priority:** 🔥 HIGH
**Effort:** 12-16 hours
**Blockers:** None (backend ready!)

---

### 3.2 Dependency Management Dashboard ⭐ MEDIUM PRIORITY

**Goal:** Admin UI to manage option dependencies

**Features:**
- [ ] **View Dependencies**
  - Table view: Option → Depends On → Type → Notes
  - Filter by dependency_type (requires, excludes, alternative)
  - Search by product model number
  
- [ ] **Add Dependencies**
  - Select Option (e.g., PK-524)
  - Select Depends On (e.g., FS-533)
  - Select Type (requires/excludes/alternative)
  - Add notes
  - Save to `option_dependencies` table
  
- [ ] **Edit/Delete Dependencies**
  - Edit existing dependencies
  - Delete invalid dependencies
  - Bulk operations
  
- [ ] **Dependency Graph Visualization**
  - Visual graph showing product → accessory relationships
  - Color-coded: green (requires), red (excludes), blue (alternative)
  - Interactive: click to see details

**API Endpoints needed:**
```python
# GET /api/dependencies
# Returns: List of all dependencies with product details

# POST /api/dependencies
# Body: { "option_id", "depends_on_option_id", "dependency_type", "notes" }
# Returns: Created dependency

# PUT /api/dependencies/{id}
# Body: { "notes": "Updated notes" }
# Returns: Updated dependency

# DELETE /api/dependencies/{id}
# Returns: Success message
```

**UI Framework:** React + TailwindCSS + React Flow (for graph)
**Priority:** 🔍 MEDIUM
**Effort:** 8-12 hours
**Blockers:** None

---

### 3.3 Accessory Compatibility Matrix 📊 MEDIUM PRIORITY

**Goal:** Visual matrix showing which accessories work with which products

**Features:**
- [ ] **Matrix View**
  - Rows: Products (bizhub C558, C658, etc.)
  - Columns: Accessories (FS-533, PK-524, RU-513, etc.)
  - Cells: ✅ compatible, ⚠️ requires other, ❌ not compatible
  
- [ ] **Filtering**
  - Filter by manufacturer
  - Filter by product type
  - Filter by accessory type
  
- [ ] **Export**
  - Export as CSV
  - Export as PDF
  - Print-friendly view

**API Endpoints needed:**
```python
# GET /api/compatibility-matrix
# Query params: manufacturer, product_type, accessory_type
# Returns: Matrix data structure
```

**UI Framework:** React + TailwindCSS + AG Grid
**Priority:** 📌 MEDIUM
**Effort:** 6-8 hours
**Blockers:** None

---

### 3.4 Product Accessories Overview 📦 LOW PRIORITY

**Goal:** Simple overview of all products and their accessories

**Features:**
- [ ] **Product List**
  - Show all products with accessories count
  - Click to expand and see accessories
  
- [ ] **Accessory Details**
  - Show accessory type
  - Show compatibility notes
  - Show if standard or optional
  
- [ ] **Quick Actions**
  - Add new accessory link
  - Edit compatibility notes
  - Mark as standard/optional

**API Endpoints needed:**
```python
# GET /api/products/{product_id}/accessories
# Returns: List of accessories with details

# POST /api/products/{product_id}/accessories
# Body: { "accessory_id", "is_standard", "compatibility_notes" }
# Returns: Created link
```

**UI Framework:** React + TailwindCSS + shadcn/ui
**Priority:** 📌 LOW
**Effort:** 4-6 hours
**Blockers:** None

---

## 🛠️ Technical Stack

### Frontend
- **Framework:** React 18 + TypeScript
- **Styling:** TailwindCSS + shadcn/ui components
- **State Management:** React Query (for API calls)
- **Routing:** React Router v6
- **Graph Visualization:** React Flow (for dependency graphs)
- **Tables:** AG Grid or TanStack Table
- **Icons:** Lucide React

### Backend (Already exists!)
- **Framework:** FastAPI (Python)
- **Database:** Supabase (PostgreSQL)
- **Validation:** `configuration_validator.py`
- **Auto-linking:** `accessory_linker.py`

### API Design
```python
# New routes to add to backend/api/routes/

# products.py
@router.get("/products/{product_id}/compatible-accessories")
@router.post("/products/{product_id}/validate-configuration")
@router.post("/products/{product_id}/save-configuration")
@router.get("/products/{product_id}/accessories")
@router.post("/products/{product_id}/accessories")

# dependencies.py (NEW FILE)
@router.get("/dependencies")
@router.post("/dependencies")
@router.put("/dependencies/{id}")
@router.delete("/dependencies/{id}")
@router.get("/dependencies/graph")

# compatibility.py (NEW FILE)
@router.get("/compatibility-matrix")
```

---

## 📊 Implementation Priority

### 🔥 Phase 3.1 (HIGH - Start First)
1. Create API endpoints for configuration validation
2. Build Product Configuration Builder UI
3. Test with existing sample data

### 🔍 Phase 3.2 (MEDIUM - After 3.1)
1. Create API endpoints for dependency management
2. Build Dependency Management Dashboard
3. Add dependency graph visualization

### 📌 Phase 3.3 & 3.4 (LOW - Nice to Have)
1. Build Compatibility Matrix
2. Build Product Accessories Overview

---

## 🎯 Success Criteria

### Must Have (MVP)
- ✅ User can select a product
- ✅ User can add accessories to configuration
- ✅ System validates configuration in real-time
- ✅ User sees errors/warnings/recommendations
- ✅ User can save configuration

### Should Have
- ✅ Admin can add/edit dependencies
- ✅ Visual dependency graph
- ✅ Compatibility matrix view

### Nice to Have
- ✅ Export configurations as PDF
- ✅ Price calculation
- ✅ Configuration templates
- ✅ Share configurations via link

---

## 📝 Example User Flow

### Scenario: Configure bizhub C558 with Finisher

1. **User selects base product:** bizhub C558
2. **System shows compatible accessories:**
   - FS-533 (Finisher) ✅
   - FS-534 (Finisher) ✅
   - PK-524 (Punch Kit) ⚠️ requires FS-533
   - RU-513 (Relay Unit) ⚠️ required for FS-534
3. **User adds FS-534 to configuration**
4. **System validates:**
   - ❌ Error: "FS-534 requires RU-513 (missing)"
5. **User adds RU-513**
6. **System validates:**
   - ✅ Valid configuration!
7. **User adds PK-524**
8. **System validates:**
   - ❌ Error: "PK-524 requires FS-533, but FS-534 is selected"
   - 💡 Recommendation: "Remove FS-534 and add FS-533, or remove PK-524"
9. **User removes PK-524**
10. **System validates:**
    - ✅ Valid configuration!
11. **User saves configuration:** "C558 with FS-534 Finisher"

---

## 🚀 Next Steps

1. **Create API endpoints** for configuration validation
2. **Set up React frontend** project
3. **Build Configuration Builder** UI (Phase 3.1)
4. **Test with sample data**
5. **Add more dependencies** to database
6. **Build Dependency Dashboard** (Phase 3.2)

---

## 📚 References

- **Backend Files:**
  - `backend/processors/accessory_linker.py`
  - `backend/utils/configuration_validator.py`
  - `backend/utils/accessory_detector.py`
  - `backend/utils/product_type_mapper.py`

- **Database:**
  - `krai_core.product_accessories` table
  - `krai_core.option_dependencies` table
  - Migration 106, 107, 108

- **Related TODOs:**
  - `TODO_PRODUCT_ACCESSORIES.md` - Phase 1 & 2 documentation
  - `TODO.md` - Main project TODO

---

**Status:** 🟢 Ready to start Phase 3!
**Next Action:** Create API endpoints for configuration validation
**Estimated Time:** 2-3 weeks for full dashboard
