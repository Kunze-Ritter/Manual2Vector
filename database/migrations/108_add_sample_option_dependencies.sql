-- Migration 108: Add sample option dependencies
-- Demonstrates the option_dependencies system with real-world examples

-- =====================================================
-- FINISHER DEPENDENCIES
-- =====================================================

-- SD-511: Saddle Stitcher Module for FS-534, FS-536
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'SD-511 Saddle Stitcher Module must be connected to FS-534 base finisher' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'SD-511'
  AND p2.model_number = 'FS-534'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'alternative' as dependency_type,
    'SD-511 can alternatively be connected to FS-536' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'SD-511'
  AND p2.model_number = 'FS-536'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- SD-512: Saddle Stitcher Module for FS-537
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'SD-512 Saddle Stitcher Module must be connected to FS-537 base finisher' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'SD-512'
  AND p2.model_number = 'FS-537'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- =====================================================
-- RELAY UNIT DEPENDENCIES (Required Bridges)
-- =====================================================

-- RU-513: Relay Unit for external finishers (FS-534 to FS-540)
-- Required for: FS-534, FS-536, FS-537, FS-539, FS-540 (external finishers)
-- NOT required for: FS-533, FS-542 (integrated finishers)

INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p2.id as option_id,  -- Finisher requires RU
    p1.id as depends_on_option_id,  -- RU is required
    'requires' as dependency_type,
    'External finisher ' || p2.model_number || ' requires RU-513 Relay Unit as bridge to main system' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'RU-513'
  AND p2.model_number IN ('FS-534', 'FS-536', 'FS-537', 'FS-539', 'FS-540')
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- RU-519: Alternative Relay Unit
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p2.id as option_id,
    p1.id as depends_on_option_id,
    'requires' as dependency_type,
    'External finisher ' || p2.model_number || ' requires RU-519 Relay Unit (alternative to RU-513)' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'RU-519'
  AND p2.model_number IN ('FS-534', 'FS-536', 'FS-537', 'FS-539', 'FS-540')
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- RU-513 vs RU-519: Alternatives
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'alternative' as dependency_type,
    'RU-513 and RU-519 are alternative relay units (choose one)' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'RU-513'
  AND p2.model_number = 'RU-519'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- =====================================================
-- PUNCH KIT DEPENDENCIES
-- =====================================================

-- PK-519, PK-520, PK-523, PK-524, PK-526: Punch Kits for Finishers
-- These require a finisher to be installed

INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'Punch Kit ' || p1.model_number || ' requires finisher ' || p2.model_number as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number IN ('PK-519', 'PK-520', 'PK-523', 'PK-524', 'PK-526')
  AND p2.model_number LIKE 'FS-%'
  AND p2.model_number IN ('FS-533', 'FS-534', 'FS-536', 'FS-537', 'FS-539', 'FS-540', 'FS-542')
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- =====================================================
-- ADVANCED FINISHING WORKFLOW DEPENDENCIES
-- =====================================================

-- TU-503: Trimmer requires SD module for booklet workflow
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'Trimmer TU-503 requires SD Saddle Stitcher Module for full booklet trimming workflow' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'TU-503'
  AND p2.model_number LIKE 'SD-%'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- CR-101: Creaser requires SD module
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'Creaser CR-101 requires SD Saddle Stitcher Module for creasing in booklet production' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'CR-101'
  AND p2.model_number LIKE 'SD-%'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- FD-503, FD-504: Folding Units require SD module
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'Folding Unit ' || p1.model_number || ' requires SD Saddle Stitcher Module for folding operations' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number IN ('FD-503', 'FD-504')
  AND p2.model_number LIKE 'SD-%'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- =====================================================
-- IMAGE CONTROLLER DEPENDENCIES
-- =====================================================

-- IC-609: Image Controller requires VI-514 Video Interface Kit
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'Image Controller IC-609 requires VI-514 Video Interface Kit for connection to AccurioPress C4080/C4070' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'IC-609'
  AND p2.model_number = 'VI-514'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- IC-318L, IC-319, IC-317, IC-419: Fiery Controllers require VI-514 or VI-515
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'Fiery Controller ' || p1.model_number || ' requires VI-514 or VI-515 Video Interface Kit' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number IN ('IC-318L', 'IC-319', 'IC-317', 'IC-419')
  AND p2.model_number IN ('VI-514', 'VI-515')
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- VI-514 vs VI-515: Alternatives
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'alternative' as dependency_type,
    'VI-514 and VI-515 are alternative video interface kits (choose based on controller and system)' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number = 'VI-514'
  AND p2.model_number = 'VI-515'
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- IC-602, IC-604, IC-605A: Older controllers require VI-505 or VI-509
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
SELECT 
    p1.id as option_id,
    p2.id as depends_on_option_id,
    'requires' as dependency_type,
    'Controller ' || p1.model_number || ' requires ' || p2.model_number || ' Video Interface Kit for bizhub PRESS systems' as notes
FROM krai_core.products p1
CROSS JOIN krai_core.products p2
WHERE p1.model_number IN ('IC-602', 'IC-604', 'IC-605A')
  AND p2.model_number IN ('VI-505', 'VI-509')
ON CONFLICT (option_id, depends_on_option_id, dependency_type) DO NOTHING;

-- =====================================================
-- SUMMARY & LOGGING
-- =====================================================

DO $$
DECLARE
    dependency_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO dependency_count
    FROM krai_core.option_dependencies;
    
    RAISE NOTICE 'Migration 108 complete: Added sample option dependencies';
    RAISE NOTICE 'Total dependencies in database: %', dependency_count;
END $$;

-- Show summary of added dependencies
SELECT 
    dependency_type,
    COUNT(*) as count
FROM krai_core.option_dependencies
GROUP BY dependency_type
ORDER BY dependency_type;
