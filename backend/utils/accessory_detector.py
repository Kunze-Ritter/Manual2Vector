"""
Accessory/Option Detection System
Detects accessories, options, and consumables and links them to compatible products
"""
import re
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class AccessoryMatch:
    """Detected accessory information"""
    model_number: str
    accessory_type: str
    product_type: str
    series_name: str
    description: str
    compatible_series: List[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'model_number': self.model_number,
            'accessory_type': self.accessory_type,
            'product_type': self.product_type,
            'series_name': self.series_name,
            'description': self.description,
            'compatible_series': self.compatible_series or []
        }


def detect_konica_minolta_accessory(model_number: str) -> Optional[AccessoryMatch]:
    """
    Detect Konica Minolta accessories/options
    
    Args:
        model_number: Model number to check (e.g., "DF-628", "FS-534", "TN-512")
        
    Returns:
        AccessoryMatch if detected, None otherwise
    """
    model = model_number.upper().strip()
    
    # Remove common prefixes
    model_clean = re.sub(r'^(?:KONICA\s+MINOLTA\s+)?', '', model).strip()
    
    # ===== FINISHING & DOCUMENT FEEDER =====
    
    # DF-* : Duplex Document Feeder
    match = re.match(r'^DF-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='document_feeder',
            product_type='document_feeder',
            series_name='DF Series',
            description=f'Konica Minolta {model_clean} Duplex Automatic Document Feeder',
            compatible_series=['bizhub']  # Compatible with bizhub series
        )
    
    # LU-* : Large Capacity Unit
    match = re.match(r'^LU-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='large_capacity_feeder',
            product_type='large_capacity_feeder',
            series_name='LU Series',
            description=f'Konica Minolta {model_clean} Large Capacity Paper Feeder',
            compatible_series=['bizhub']
        )
    
    # FS-* : Finisher (Stapling, Booklet, etc.)
    match = re.match(r'^FS-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='finisher',
            product_type='finisher',
            series_name='FS Series',
            description=f'Konica Minolta {model_clean} Finisher (Stapling/Booklet)',
            compatible_series=['bizhub']
        )
    
    # SD-* : Saddle Stitch Unit (Booklet)
    match = re.match(r'^SD-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='booklet_finisher',
            product_type='booklet_finisher',
            series_name='SD Series',
            description=f'Konica Minolta {model_clean} Saddle Stitch/Booklet Unit',
            compatible_series=['bizhub']
        )
    
    # PK-* : Punch Kit
    match = re.match(r'^PK-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='punch_finisher',
            product_type='punch_finisher',
            series_name='PK Series',
            description=f'Konica Minolta {model_clean} Hole Punch Kit',
            compatible_series=['bizhub']
        )
    
    # PH-* : Punch Hole Unit
    match = re.match(r'^PH-(\d{3,4}[A-Z]?)$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='punch_finisher',
            product_type='punch_finisher',
            series_name='PH Series',
            description=f'Konica Minolta {model_clean} Punch Hole Unit',
            compatible_series=['bizhub']
        )
    
    # ZF-* : Z-Fold Unit
    match = re.match(r'^ZF-(\d{3,4})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='fold_unit',
            product_type='fold_unit',
            series_name='ZF Series',
            description=f'Konica Minolta {model_clean} Z-Fold Unit',
            compatible_series=['bizhub']
        )
    
    # BF-* : Banner Feeder
    match = re.match(r'^BF-(\d{3,4})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='banner_feeder',
            product_type='banner_feeder',
            series_name='BF Series',
            description=f'Konica Minolta {model_clean} Banner Feeder',
            compatible_series=['bizhub']
        )
    
    # AK-* : Auto Keycard Reader / Authentication Kit
    match = re.match(r'^AK-?(\d{3,4})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='authentication_kit',
            product_type='authentication_kit',
            series_name='AK Series',
            description=f'Konica Minolta {model_clean} Auto Keycard Reader/Authentication Kit',
            compatible_series=['bizhub']
        )
    
    # JS-* : Job Separator
    match = re.match(r'^JS-?(\d{3,4})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='job_separator',
            product_type='job_separator',
            series_name='JS Series',
            description=f'Konica Minolta {model_clean} Job Separator',
            compatible_series=['bizhub']
        )
    
    # IS-* : Inner Shift Tray / Inner Finisher
    match = re.match(r'^IS-(\d{3,4})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='inner_finisher',
            product_type='inner_finisher',
            series_name='IS Series',
            description=f'Konica Minolta {model_clean} Inner Shift Tray/Finisher',
            compatible_series=['bizhub']
        )
    
    # DP-* : Document Processor (NOT Document Feeder!)
    match = re.match(r'^DP-(\d{3,4})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='document_processor',
            product_type='document_processor',
            series_name='DP Series',
            description=f'Konica Minolta {model_clean} Document Processor',
            compatible_series=['bizhub']
        )
    
    # ===== PAPER FEEDERS/CASSETTES =====
    
    # PC-* : Paper Feed Unit/Cassette
    match = re.match(r'^PC-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='paper_feeder',
            product_type='paper_feeder',
            series_name='PC Series',
            description=f'Konica Minolta {model_clean} Paper Feed Unit/Cassette',
            compatible_series=['bizhub']
        )
    
    # PF-* : Paper Tray/Cassette
    match = re.match(r'^PF-P(\d{2})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='paper_feeder',
            product_type='paper_feeder',
            series_name='PF Series',
            description=f'Konica Minolta {model_clean} Paper Tray/Cassette',
            compatible_series=['bizhub']
        )
    
    # MT-* : Mailbox/Sorter
    match = re.match(r'^MT-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='mailbox',
            product_type='mailbox',
            series_name='MT Series',
            description=f'Konica Minolta {model_clean} Mailbox/Sorter',
            compatible_series=['bizhub']
        )
    
    # ===== FAX & CONNECTIVITY =====
    
    # FK-* : Fax Kit
    match = re.match(r'^FK-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='fax_kit',
            product_type='fax_kit',
            series_name='FK Series',
            description=f'Konica Minolta {model_clean} Fax Expansion Kit',
            compatible_series=['bizhub']
        )
    
    # MK-* : Mounting Kit/Installation Kit
    match = re.match(r'^MK-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='accessory',
            product_type='accessory',
            series_name='MK Series',
            description=f'Konica Minolta {model_clean} Mounting/Installation Kit',
            compatible_series=['bizhub']
        )
    
    # RU-* : Relay Unit
    match = re.match(r'^RU-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='accessory',
            product_type='accessory',
            series_name='RU Series',
            description=f'Konica Minolta {model_clean} Relay Unit (Bypass/Separator)',
            compatible_series=['bizhub']
        )
    
    # CU-* : Cleaning Unit
    match = re.match(r'^CU-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='maintenance_kit',
            product_type='maintenance_kit',
            series_name='CU Series',
            description=f'Konica Minolta {model_clean} Cleaning Unit',
            compatible_series=['bizhub']
        )
    
    # ===== MEMORY, HDD, WIRELESS =====
    
    # HD-* : Hard Disk Drive
    match = re.match(r'^HD-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='hard_drive',
            product_type='hard_drive',
            series_name='HD Series',
            description=f'Konica Minolta {model_clean} Hard Disk Drive',
            compatible_series=['bizhub']
        )
    
    # EK-* : Card Reader/Authentication Kit
    match = re.match(r'^EK-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='card_reader',
            product_type='card_reader',
            series_name='EK Series',
            description=f'Konica Minolta {model_clean} Card Reader/Authentication Kit',
            compatible_series=['bizhub']
        )
    
    # WT-* : Waste Toner Box
    match = re.match(r'^WT-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='waste_toner_box',
            product_type='waste_toner_box',
            series_name='WT Series',
            description=f'Konica Minolta {model_clean} Waste Toner Container',
            compatible_series=['bizhub']
        )
    
    # AU-* : Authentication Module
    match = re.match(r'^AU-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='card_reader',
            product_type='card_reader',
            series_name='AU Series',
            description=f'Konica Minolta {model_clean} Authentication Module (e.g., Fingerprint)',
            compatible_series=['bizhub']
        )
    
    # UK-* : USB Kit
    match = re.match(r'^UK-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='interface_kit',
            product_type='interface_kit',
            series_name='UK Series',
            description=f'Konica Minolta {model_clean} USB Interface Kit',
            compatible_series=['bizhub']
        )
    
    # ===== TONER/INK & CONSUMABLES =====
    
    # TN-* : Toner Cartridge
    match = re.match(r'^TN-(\d{3})([A-Z]?)$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='toner_cartridge',
            product_type='toner_cartridge',
            series_name='TN Series',
            description=f'Konica Minolta {model_clean} Toner Cartridge',
            compatible_series=['bizhub']
        )
    
    # DR-* : Drum Unit
    match = re.match(r'^DR-(\d{3})([A-Z]?)$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='drum_unit',
            product_type='drum_unit',
            series_name='DR Series',
            description=f'Konica Minolta {model_clean} Drum/Imaging Unit',
            compatible_series=['bizhub']
        )
    
    # SK-* : Staples
    match = re.match(r'^SK-(\d{3})$', model_clean)
    if match:
        return AccessoryMatch(
            model_number=model_clean,
            accessory_type='staple_cartridge',
            product_type='staple_cartridge',
            series_name='SK Series',
            description=f'Konica Minolta {model_clean} Staple Cartridge',
            compatible_series=['bizhub']
        )
    
    return None


def detect_accessory(model_number: str, manufacturer: str = None) -> Optional[AccessoryMatch]:
    """
    Main accessory detection function
    
    Args:
        model_number: Model number to check
        manufacturer: Manufacturer name (optional, helps with detection)
        
    Returns:
        AccessoryMatch if detected, None otherwise
    """
    if not model_number:
        return None
    
    # Normalize manufacturer
    if manufacturer:
        manufacturer_lower = manufacturer.lower().strip()
    else:
        manufacturer_lower = ''
    
    # Konica Minolta accessories
    if 'konica' in manufacturer_lower or 'minolta' in manufacturer_lower or not manufacturer:
        result = detect_konica_minolta_accessory(model_number)
        if result:
            return result
    
    # TODO: Add other manufacturers' accessories here
    # - HP accessories
    # - Xerox accessories
    # - Ricoh accessories
    # etc.
    
    return None
