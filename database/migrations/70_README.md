# Migration 70: Optimize Product Types

## Purpose

Optimize and expand the `product_type` constraint to include:
1. **Remove redundant generic types** (`printer` → use specific types)
2. **Add dot_matrix_printer** for legacy printers
3. **Add comprehensive accessories** (keyboard, card_reader, fax_kit, etc.)
4. **Add finisher types** (stapler, booklet, punch, folder, trimmer)
5. **Add feeder types** (paper, envelope, LCF, ADF)
6. **Add consumable types** (toner, ink, drum, fuser, etc.)
7. **Add software types** (software, license, firmware)

## Changes

### Removed
- ❌ Generic `printer` (use specific: laser_printer, inkjet_printer, etc.)

### Added Printers
- ✅ `dot_matrix_printer` - Dot matrix/impact printers (Lexmark Plus 2380)
- ✅ `thermal_printer` - Thermal transfer printers (Zebra, Brother QL)
- ✅ `dye_sublimation_printer` - Dye-sub photo printers

### Added Multifunction
- ✅ `production_multifunction` - Production MFP systems

### Added Plotters
- ✅ `pen_plotter` - Mechanical pen plotters (legacy)

### Added Scanners
- ✅ `document_scanner` - Document/ADF scanners
- ✅ `photo_scanner` - Photo/flatbed scanners
- ✅ `large_format_scanner` - A0/A1 scanners

### Added Finishers
- ✅ `stapler_finisher` - Stapler finisher
- ✅ `booklet_finisher` - Booklet/saddle-stitch finisher
- ✅ `punch_finisher` - Hole punch finisher
- ✅ `folder` - Folder unit
- ✅ `trimmer` - Trimmer unit
- ✅ `stacker` - Output stacker

### Added Feeders
- ✅ `paper_feeder` - Paper cassette/tray
- ✅ `envelope_feeder` - Envelope feeder
- ✅ `large_capacity_feeder` - LCF/HCF
- ✅ `document_feeder` - ADF

### Added Accessories
- ✅ `cabinet` - Cabinet/stand
- ✅ `work_table` - Work table
- ✅ `caster_base` - Caster base/wheels
- ✅ `bridge_unit` - Bridge unit
- ✅ `interface_kit` - Network/USB interface
- ✅ `memory_upgrade` - RAM upgrade
- ✅ `hard_drive` - Internal HDD
- ✅ `controller` - Print controller/DFE
- ✅ `fax_kit` - Fax expansion kit
- ✅ `wireless_kit` - Wi-Fi kit
- ✅ `keyboard` - Keyboard unit
- ✅ `card_reader` - Card reader (RFID/NFC)
- ✅ `coin_kit` - Coin/payment kit

### Added Options
- ✅ `duplex_unit` - Duplex unit
- ✅ `output_tray` - Output tray
- ✅ `mailbox` - Mailbox sorter
- ✅ `job_separator` - Job separator

### Added Consumables
- ✅ `toner_cartridge` - Toner cartridge
- ✅ `ink_cartridge` - Ink cartridge
- ✅ `drum_unit` - Drum/imaging unit
- ✅ `developer_unit` - Developer unit
- ✅ `fuser_unit` - Fuser/fixing unit
- ✅ `transfer_belt` - Transfer belt/unit
- ✅ `waste_toner_box` - Waste toner container
- ✅ `maintenance_kit` - Maintenance kit
- ✅ `staple_cartridge` - Staple cartridge
- ✅ `punch_kit` - Punch waste box/kit
- ✅ `print_head` - Print head (inkjet)
- ✅ `ink_tank` - Ink tank (refillable)
- ✅ `paper` - Paper

### Added Software
- ✅ `software` - Software package
- ✅ `license` - Software license
- ✅ `firmware` - Firmware update

## Total Product Types

**Before**: 18 types
**After**: 76 types

## How to Apply

```bash
# Apply migration
psql -h localhost -U postgres -d krai -f database/migrations/70_optimize_product_types.sql

# Or via Supabase CLI
supabase db push
```

## Rollback

```sql
-- Rollback to previous constraint
ALTER TABLE krai_core.products 
DROP CONSTRAINT IF EXISTS product_type_check;

ALTER TABLE krai_core.products 
ADD CONSTRAINT product_type_check CHECK (
    product_type IN (
        'printer', 'scanner', 'multifunction', 'copier', 'plotter',
        'accessory', 'option', 'consumable', 'finisher', 'feeder',
        'laser_printer', 'inkjet_printer', 'production_printer', 'solid_ink_printer',
        'laser_multifunction', 'inkjet_multifunction',
        'inkjet_plotter', 'latex_plotter'
    )
);
```

## Impact

### Code Changes Required
- ✅ `product_type_mapper.py` - Updated to use `dot_matrix_printer`
- ✅ No other code changes needed (new types are optional)

### Database
- ✅ Existing data remains valid
- ✅ New types available for future products
- ✅ Index created for better performance

## Testing

```python
# Test new types
from utils.product_type_mapper import get_product_type

# Dot matrix
assert get_product_type('Plus Matrix Series') == 'dot_matrix_printer'

# Existing types still work
assert get_product_type('LaserJet Pro') == 'laser_printer'
assert get_product_type('AccurioPress') == 'production_printer'
```

## Benefits

1. **More Specific Classification**: Accessories, finishers, feeders now have specific types
2. **Better Analytics**: Can filter by specific product categories
3. **Parts Catalog Support**: Can classify parts/accessories properly
4. **Future-Proof**: Covers all common printer ecosystem products
5. **No Breaking Changes**: All existing types remain valid
