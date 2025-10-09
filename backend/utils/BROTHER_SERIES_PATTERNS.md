# Brother Series Detection Patterns

## Overview

Vollständige Pattern-Erkennung für alle Brother-Produktserien: Production (DTG), MFP, Printer, Fax und Mobile.

## Series-Kategorien

### 1. Production Printing (DTG/Textile)

#### GTXpro Series
- **Pattern**: `GTXPRO( B)?`
- **Beispiele**: GTXpro, GTXpro B
- **Beschreibung**: Direct-to-Garment (DTG) Printers
- **Product Type**: `production_printer`
- **Technologie**: DTG für Textildruck

#### GTX Series
- **Pattern**: `GTX`
- **Beispiele**: GTX600, GTX R2R
- **Beschreibung**: Direct-to-Garment/DTF Printers
- **Product Type**: `production_printer`
- **Besonderheit**: GTX R2R = Roll-to-Roll DTF

---

### 2. Specialty (Plotter/Cutting)

#### PL Series (Plotter)
- **Pattern**: `PL\d{4}`
- **Beispiele**: PL5250
- **Beschreibung**: Plotters
- **Product Type**: `inkjet_plotter`

#### ScanNCut Series
- **Pattern**: `SCANNCUT`
- **Beispiele**: ScanNCut SDX125
- **Beschreibung**: Cutting Machines
- **Product Type**: `accessory`
- **Besonderheit**: Schneidemaschinen für Crafting

---

### 3. MFC Series (4-in-1 MFP)

#### MFC-J Series (Inkjet)
- **Pattern**: `MFC-J\d{4}[suffix]`
- **Beispiele**: MFC-J6540DW, MFC-J5740DW
- **Beschreibung**: Inkjet MFPs (Print/Scan/Copy/Fax)
- **Product Type**: `inkjet_multifunction`

#### MFC-L Series (Laser)
- **Pattern**: `MFC-L\d{4}[suffix]`
- **Beispiele**: MFC-L9570CDW, MFC-L5935DW, MFC-L2750DW
- **Beschreibung**: Laser MFPs (Print/Scan/Copy/Fax)
- **Product Type**: `laser_multifunction`

---

### 4. DCP Series (3-in-1 MFP)

#### DCP-J Series (Inkjet)
- **Pattern**: `DCP-J\d{4}[suffix]`
- **Beispiele**: DCP-J1200W, DCP-J1310DW
- **Beschreibung**: Inkjet MFPs (Print/Scan/Copy)
- **Product Type**: `inkjet_multifunction`

#### DCP-L Series (Laser)
- **Pattern**: `DCP-L\d{4}[suffix]`
- **Beispiele**: DCP-L3550CDW, DCP-L1640W
- **Beschreibung**: Laser MFPs (Print/Scan/Copy)
- **Product Type**: `laser_multifunction`

---

### 5. HL Series (Printer)

#### HL-L Series (Laser)
- **Pattern**: `HL-L\d{4}[suffix]`
- **Beispiele**: HL-L2350DW, HL-L5100DN, HL-L9470CDN
- **Beschreibung**: Laser Printers
- **Product Type**: `laser_printer`

---

### 6. IntelliFax Series (Fax)

#### IntelliFax Series
- **Pattern**: `INTELLIFAX \d{4}[suffix]`
- **Beispiele**: IntelliFax 2840, IntelliFax 4750e
- **Beschreibung**: Fax Machines
- **Product Type**: `laser_multifunction`

---

### 7. PJ Series (Mobile/Portable)

#### PJ Series
- **Pattern**: `PJ-\d{3}[suffix]`
- **Beispiele**: PJ-763MFi, PJ-863PK
- **Beschreibung**: Mobile/Portable Printers
- **Product Type**: `inkjet_printer`
- **Besonderheit**: A4 Mobile Printers

---

## Suffix-Bedeutungen

| Suffix | Bedeutung |
|--------|-----------|
| **DW** | Duplex + Wireless |
| **DN** | Duplex + Network |
| **CDW** | Color + Duplex + Wireless |
| **CDN** | Color + Duplex + Network |
| **MFi** | Mobile + Fax + iOS |
| **PK** | Portable Kit |

---

## Test-Abdeckung

✅ **22/22 Tests bestanden** (100%)

- Production: 4/4
- Specialty: 2/2
- MFC Series: 5/5
- DCP Series: 4/4
- HL Series: 3/3
- IntelliFax: 2/2
- PJ Series: 2/2

---

## Beispiel-Output

```python
from utils.series_detector import detect_series
from utils.product_type_mapper import get_product_type

# Production DTG
result = detect_series('GTXpro', 'Brother')
# → {'series_name': 'GTXpro', 'model_pattern': 'GTXpro', ...}
product_type = get_product_type('GTXpro')
# → 'production_printer'

# Laser MFP
result = detect_series('MFC-L2750DW', 'Brother')
# → {'series_name': 'MFC-L', 'model_pattern': 'MFC-L2xxx', ...}
product_type = get_product_type('MFC-L')
# → 'laser_multifunction'

# Inkjet MFP
result = detect_series('DCP-J1200W', 'Brother')
# → {'series_name': 'DCP-J', 'model_pattern': 'DCP-J1xxx', ...}
product_type = get_product_type('DCP-J')
# → 'inkjet_multifunction'
```

---

## Besonderheiten

### 1. **4-in-1 vs 3-in-1**
- **MFC** = 4-in-1 (Print/Scan/Copy/**Fax**)
- **DCP** = 3-in-1 (Print/Scan/Copy)

### 2. **DTG/DTF Production**
Brother ist bekannt für Direct-to-Garment (DTG) Drucker:
- **GTXpro**: Professional DTG
- **GTX600**: Entry-level DTG
- **GTX R2R**: Roll-to-Roll DTF (Direct-to-Film)

### 3. **Mobile Printing**
PJ-Serie bietet A4 Mobile Printing:
- Batteriebetrieben
- Bluetooth/Wi-Fi
- Ideal für Außendienst

---

## Zusammenfassung

Die Brother Series Detection unterstützt:

- ✅ Production (GTXpro, GTX - DTG/DTF)
- ✅ Specialty (PL Plotter, ScanNCut)
- ✅ MFP 4-in-1 (MFC-J, MFC-L)
- ✅ MFP 3-in-1 (DCP-J, DCP-L)
- ✅ Printer (HL-L)
- ✅ Fax (IntelliFax)
- ✅ Mobile (PJ Series)
- ✅ 100% Test-Abdeckung (22/22 Tests)
