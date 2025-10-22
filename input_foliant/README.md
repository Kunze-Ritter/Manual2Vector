# Foliant PDF Input Directory

This directory contains **Konica Minolta Foliant PDFs** for automatic import into the KRAI database.

## What are Foliant PDFs?

Foliant PDFs are **interactive configuration tools** provided by Konica Minolta. They contain:

- ✅ Complete product lists (bizhub models)
- ✅ All compatible accessories (finishers, feeders, trays, etc.)
- ✅ Article codes for ordering
- ✅ Compatibility matrices
- ✅ Physical specifications (dimensions, weight, power)

## How to Use

### 1. Place Foliant PDFs here

Download Foliant PDFs from Konica Minolta and place them in this directory:

```
input_foliant/
  ├── Foliant bizhub C257i v1.10 R1.pdf
  ├── Foliant bizhub C454e v2.0.pdf
  ├── Foliant bizhub C759 v1.5.pdf
  └── ...
```

### 2. Run the Import Script

```bash
# From project root:
python scripts/import_foliant_to_db.py
```

The script will:
- ✅ Automatically find all PDFs in this directory
- ✅ Extract product and accessory data
- ✅ Import into `krai_core.products` table
- ✅ Classify accessories (finisher, feeder, tray, etc.)
- ✅ Store article codes in `specifications.article_code`

### 3. Check Results

```bash
# Summary will show:
Files processed: 3
  Successful: 3
  Failed: 0
Total articles imported: 150
```

## Where to Find Foliant PDFs

**Konica Minolta Internal:**
- Sales Portal
- Product Configuration Tools
- Technical Documentation Library

**File Naming:**
- Format: `Foliant bizhub <MODEL> v<VERSION>.pdf`
- Example: `Foliant bizhub C257i v1.10 R1.pdf`

## What Gets Imported

### Main Products
- **Models:** C227i, C257i, C287i, C454e, C554e, C654e, C754e, etc.
- **Type:** Automatically set to `laser_multifunction`
- **Article Code:** Stored in `specifications.article_code`

### Accessories
- **Finishers:** FS-533, FS-539, FS-539SD, etc.
- **Feeders:** DF-633, etc.
- **Trays:** PK-519, PK-524, OT-506, etc.
- **Cabinets:** PC-118, PC-218, PC-418, DK-518, etc.
- **Other:** AU-102, CU-101, RU-514, etc.

All accessories are:
- ✅ Automatically classified by type
- ✅ Linked to manufacturer (Konica Minolta)
- ✅ Stored with article codes

## Troubleshooting

### No PDFs found
```
No PDF files found in: input_foliant/
```
→ Place Foliant PDFs in this directory

### Extraction failed
```
ERROR processing Foliant.pdf: ...
```
→ Check if PDF is a valid Foliant PDF (has "Pandora" field)
→ Check if PDF is encrypted (should work with standard encryption)

### No data extracted
```
No data extracted!
```
→ PDF might not be a Foliant PDF
→ Check PDF structure with `scripts/extract_pdf_javascript.py`

## Technical Details

**Extraction Method:**
1. Parse PDF AcroForm fields
2. Find "Pandora" field (contains XML/CSV data)
3. Extract article codes table
4. Parse product names and codes
5. Classify main products vs accessories
6. Import to database

**Data Format in PDF:**
```
name;code
C227i;ACM2021
C257i;ACVD021
FS-539;A3EPWY2
PK-524;A3ETW21
...
```

## Next Steps

After import, you can:
- ✅ View products in database: `SELECT * FROM vw_products WHERE manufacturer_id = '<konica_minolta_id>'`
- ✅ Check article codes: `SELECT model_number, specifications->>'article_code' FROM vw_products`
- ✅ Link accessories to products (manual or automatic)
- ✅ Use for agent queries about compatible options

---

**Last Updated:** 2025-10-22
**Script:** `scripts/import_foliant_to_db.py`
