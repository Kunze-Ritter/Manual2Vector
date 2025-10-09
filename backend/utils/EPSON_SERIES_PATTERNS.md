# Epson Series Detection Patterns

## Overview

Vollständige Pattern-Erkennung für alle Epson-Produktserien: Production, Professional, Office, Home und Legacy.

## Series-Kategorien

### 1. Production Printing

#### SureColor Production (SC-P9xxx)
- **Pattern**: `SC-P9\d{3}`
- **Beispiele**: SureColor SC-P9500
- **Beschreibung**: Production Large Format Printers
- **Product Type**: `production_printer`

#### SureColor F (Textile/Sublimation)
- **Pattern**: `SC-F\d{4}`
- **Beispiele**: SC-F9400, SC-F6300
- **Beschreibung**: Textile/Sublimation Production Printers
- **Product Type**: `production_printer`
- **Technologie**: Dye-Sublimation für Textildruck

#### Monna Lisa (Industrial Textile)
- **Pattern**: `MONNA LISA`
- **Beispiele**: Monna Lisa ML-8000
- **Beschreibung**: Industrial Textile Printers
- **Product Type**: `production_printer`

#### SureLab (Photo Production)
- **Pattern**: `SURELAB`
- **Beispiele**: SureLab D700
- **Beschreibung**: Professional Photo Production Systems (MiniLab)
- **Product Type**: `production_printer`

---

### 2. SureColor Professional (Large Format)

#### SureColor P Series
- **Pattern**: `SC-P\d{3,4}`
- **Beispiele**: SC-P600, SC-P800, SC-P7300
- **Beschreibung**: Professional Large Format Printers
- **Product Type**: `inkjet_plotter`
- **Zielgruppe**: Fotografie, Grafik, CAD

---

### 3. WorkForce (Office/Business)

#### WorkForce Enterprise
- **Pattern**: `WORKFORCE ENTERPRISE WF-C\d{5}`
- **Beispiele**: WorkForce Enterprise WF-C17590
- **Beschreibung**: High-volume Inkjet MFPs
- **Product Type**: `inkjet_multifunction`

#### WorkForce Pro
- **Pattern**: `(WORKFORCE )?PRO WF-\d{4}[suffix]`
- **Beispiele**: Pro WF-4745, Pro WF-5620, WF-4745DWF, WF-8510DWF
- **Beschreibung**: Professional Inkjet MFPs
- **Product Type**: `inkjet_multifunction`

#### WorkForce Standard
- **Pattern**: `(WORKFORCE )?WF-\d{4}`
- **Beispiele**: WF-2830, WF-2850, WF-7840
- **Beschreibung**: Office Inkjet MFPs
- **Product Type**: `inkjet_multifunction`

---

### 4. EcoTank (Refillable Ink)

#### EcoTank Series
- **Pattern**: `(ECOTANK )?ET-\d{4}`
- **Beispiele**: ET-2750, ET-7700, ET-2850, ET-3850, ET-5880
- **Beschreibung**: Refillable Ink Tank Printers/MFPs
- **Product Type**: `inkjet_multifunction`
- **Besonderheit**: Nachfüllbare Tintentanks statt Patronen

---

### 5. Expression (Home/Photo)

#### Expression Photo
- **Pattern**: `(EXPRESSION )?PHOTO XP-\d{4}`
- **Beispiele**: Expression Photo XP-8700
- **Beschreibung**: Photo Printers
- **Product Type**: `inkjet_printer`

#### Expression Home
- **Pattern**: `(EXPRESSION )?HOME XP-\d{3,4}`
- **Beispiele**: XP-2200, XP-332, XP-5200
- **Beschreibung**: Home Inkjet Printers/MFPs
- **Product Type**: `inkjet_multifunction`

---

### 6. Stylus (Legacy)

#### Stylus Photo
- **Pattern**: `(STYLUS )?PHOTO PX\d{3}[suffix]`
- **Beispiele**: Stylus Photo PX700W, PX710W
- **Beschreibung**: Photo Printers (Legacy)
- **Product Type**: `inkjet_printer`

#### Stylus Pro
- **Pattern**: `(STYLUS )?PRO`
- **Beispiele**: Stylus Pro 9900
- **Beschreibung**: Large Format Printers (Legacy, replaced by SureColor)
- **Product Type**: `inkjet_plotter`

#### Stylus General
- **Pattern**: `STYLUS`
- **Beschreibung**: General Stylus Printers (Legacy)
- **Product Type**: `inkjet_printer`

---

### 7. Legacy Matrix/Office

#### MJ Series (Dot Matrix)
- **Pattern**: `MJ-`
- **Beispiele**: MJ-500
- **Beschreibung**: Dot Matrix Printers (Legacy)
- **Product Type**: `dot_matrix_printer`

#### MX/MP/P Series (Office)
- **Pattern**: `MX-\d{3,4}`, `MP-\d{3,4}`, `P-\d{3,4}`
- **Beispiele**: MX-1000, MP-2000, P-3000
- **Beschreibung**: Office Printers (Legacy)
- **Product Type**: `inkjet_printer`

---

## Test-Abdeckung

✅ **24/24 Tests bestanden** (100%)

- Production: 5/5
- SureColor Professional: 3/3
- WorkForce: 5/5
- EcoTank: 4/4
- Expression: 3/3
- Stylus: 2/2
- Legacy: 2/2

---

## Beispiel-Output

```python
from utils.series_detector import detect_series
from utils.product_type_mapper import get_product_type

# Production
result = detect_series('SureColor SC-P9500', 'Epson')
# → {'series_name': 'SureColor Production', ...}
product_type = get_product_type('SureColor Production')
# → 'production_printer'

# EcoTank
result = detect_series('EcoTank ET-2850', 'Epson')
# → {'series_name': 'EcoTank', 'model_pattern': 'EcoTank ET-2xxx', ...}
product_type = get_product_type('EcoTank')
# → 'inkjet_multifunction'

# Professional Large Format
result = detect_series('SC-P7300', 'Epson')
# → {'series_name': 'SureColor P', ...}
product_type = get_product_type('SureColor P')
# → 'inkjet_plotter'
```

---

## Zusammenfassung

Die Epson Series Detection unterstützt:

- ✅ Production (SureColor Production, SureColor F, Monna Lisa, SureLab)
- ✅ Professional (SureColor P)
- ✅ Office (WorkForce Enterprise/Pro/Standard)
- ✅ Home (EcoTank, Expression Home/Photo)
- ✅ Legacy (Stylus, MJ/MX/MP/P)
- ✅ 100% Test-Abdeckung (24/24 Tests)
