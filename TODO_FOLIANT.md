# TODO: FOLIANT COMPATIBILITY SYSTEM

**Last Updated:** 2025-10-22 (16:35)

## ✅ COMPLETED

- [x] **Extract all sprites from Foliant PDF** ✅ (16:26)
  - Extracted 38 available options from C257i PDF
  - **File:** `scripts/extract_all_sprites.py`
  - **Result:** Complete list of configurable options

- [x] **Build compatibility matrix** ✅ (16:30)
  - Categorized by mounting position (top/side/bottom/internal/accessory)
  - **Files:** `scripts/build_compatibility_matrix.py`, `FOLIANT_COMPATIBILITY_MATRIX.md`
  - **Result:** Complete compatibility rules for all products

- [x] **Create Migration 111** ✅ (16:32)
  - Added `mounting_position`, `slot_number`, `max_quantity` to product_accessories
  - **File:** `database/migrations/111_add_mounting_position_and_slots.sql`
  - **Result:** DB ready for mounting positions and slots

- [x] **Solve FK-513_1/_2 problem** ✅ (16:32)
  - Use slot_number instead of duplicate products
  - **Result:** Only 1x FK-513 in DB, 2x entries in product_accessories

## 🔥 HIGH PRIORITY

- [ ] **Add requires_accessory_id for dependencies** 🔥
  - **Task:** Add column to track which accessories require others
  - **Example:** FS-539 requires RU-514 (Relay Unit)
  - **Files to modify:**
    - `database/migrations/112_add_accessory_dependencies.sql`
    - `scripts/import_foliant_to_db.py` (parse dependencies)
  - **Priority:** HIGH
  - **Effort:** 2-3 hours
  - **Status:** TODO

- [ ] **Dashboard: Foliant PDF Upload** 🔥
  - **Task:** Add upload endpoint for Foliant PDFs
  - **Implementation:**
    ```python
    @app.post("/api/foliant/upload")
    async def upload_foliant_pdf(file: UploadFile):
        # Save, process, import
        data = extract_foliant_data(pdf_path)
        success = import_to_database(data)
        return {"success": success, "stats": {...}}
    ```
  - **Files to modify:**
    - `backend/api/foliant_api.py` (new file)
    - `frontend/src/pages/FoliantUpload.tsx` (new file)
  - **Priority:** HIGH
  - **Effort:** 3-4 hours
  - **Status:** TODO

- [ ] **Agent: Compatibility validation** 🔥
  - **Task:** Agent can validate if configuration is possible
  - **Example:** "Kann ich C257i mit FS-539 + DF-633 + PC-418 konfigurieren?"
  - **Implementation:**
    - Query product_accessories with mounting_position
    - Check max_quantity limits
    - Check dependencies (requires_accessory_id)
  - **Files to modify:**
    - `backend/api/agent_api.py` (add compatibility_check function)
    - Agent prompt with compatibility rules
  - **Priority:** HIGH
  - **Effort:** 4-5 hours
  - **Status:** TODO

## 🔍 MEDIUM PRIORITY

- [ ] **Parse dependencies from Foliant JavaScript** 🔍
  - **Task:** Extract requires/depends logic from PDF JavaScript
  - **Example:** Find which accessories require others
  - **Files to modify:**
    - `scripts/extract_all_javascript.py` (parse Registry.System.Logic.Groups)
  - **Priority:** MEDIUM
  - **Effort:** 3-4 hours
  - **Status:** TODO

- [x] **Mutual exclusivity rules** ✅ (16:40)
  - **Task:** Clarify mutual exclusivity logic
  - **Result:** Mounting positions are COMPATIBLE with each other!
    - TOP + SIDE + BOTTOM + INTERNAL + ACCESSORY = all can be combined
    - Only WITHIN same position: max_quantity defines exclusivity
    - Example: PC-118 vs PC-218 (both BOTTOM, only 1x allowed)
  - **Files updated:**
    - `docs/FOLIANT_SYSTEM.md` (clarified logic)
  - **Priority:** MEDIUM
  - **Effort:** 1 hour
  - **Status:** DONE

- [ ] **Process all Foliant PDFs** 🔍
  - **Task:** Import all PDFs from input_foliant/
  - **Current:** Only C257i processed
  - **Files to process:**
    - AccurioPress 7136-7136P-7120
    - bizhub C251i-C361i-C451i-C551i-C651i-C751i
    - bizhub 301i-361i-451i-551i-651i-751i
    - ... and more
  - **Priority:** MEDIUM
  - **Effort:** 1-2 hours (automated)
  - **Status:** TODO

## 📌 LOW PRIORITY

- [ ] **Quantity limits per accessory** 📌
  - **Task:** Some accessories have their own max quantity
  - **Example:** "Max 2x PK-519 punch kits"
  - **Implementation:**
    - Already have `max_quantity` column
    - Need to parse from Foliant
  - **Priority:** LOW
  - **Effort:** 2 hours
  - **Status:** TODO

- [ ] **Visual configuration builder** 📌
  - **Task:** UI to visually build configurations
  - **Features:**
    - Drag & drop accessories
    - Real-time compatibility check
    - Show mounting positions
  - **Files to create:**
    - `frontend/src/pages/ConfigurationBuilder.tsx`
  - **Priority:** LOW
  - **Effort:** 8-10 hours
  - **Status:** TODO

## 📊 Statistics

**Session:** 2025-10-22 (14:00-16:35)
**Time:** ~2.5 hours
**Commits:** 5+ commits
**Files Created:** 18+ files
**Migrations:** 2 (110, 111)

**Key Achievements:**
1. ✅ Complete Foliant compatibility matrix extracted
2. ✅ Mounting position system implemented
3. ✅ Slot system for duplicate accessories (FK-513_1/_2)
4. ✅ 38 options categorized and documented
5. ✅ Foundation for Agent compatibility checks

**Next Focus:**
- Dashboard upload endpoint 🎯
- Agent compatibility validation 🎯
- Dependencies parsing 🎯
