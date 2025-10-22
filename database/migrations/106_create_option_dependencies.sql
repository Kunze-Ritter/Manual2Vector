-- Migration 106: Create option_dependencies table
-- Models complex relationships between accessories/options
-- Use cases: requires, excludes, alternatives

-- Create option_dependencies table
CREATE TABLE IF NOT EXISTS krai_core.option_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    option_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    depends_on_option_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    dependency_type VARCHAR(20) NOT NULL CHECK (dependency_type IN ('requires', 'excludes', 'alternative')),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Prevent self-dependencies
    CONSTRAINT no_self_dependency CHECK (option_id != depends_on_option_id),
    
    -- Unique constraint: one dependency type per option pair
    CONSTRAINT unique_option_dependency UNIQUE (option_id, depends_on_option_id, dependency_type)
);

-- Create indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_option_dependencies_option_id 
    ON krai_core.option_dependencies(option_id);
    
CREATE INDEX IF NOT EXISTS idx_option_dependencies_depends_on 
    ON krai_core.option_dependencies(depends_on_option_id);
    
CREATE INDEX IF NOT EXISTS idx_option_dependencies_type 
    ON krai_core.option_dependencies(dependency_type);

-- Add RLS (Row Level Security)
ALTER TABLE krai_core.option_dependencies ENABLE ROW LEVEL SECURITY;

-- Policy: Allow service_role full access
CREATE POLICY option_dependencies_service_role_all 
    ON krai_core.option_dependencies 
    FOR ALL 
    TO service_role 
    USING (true) 
    WITH CHECK (true);

-- Policy: Allow authenticated users read access
CREATE POLICY option_dependencies_authenticated_read 
    ON krai_core.option_dependencies 
    FOR SELECT 
    TO authenticated 
    USING (true);

-- Create view for easy querying
CREATE OR REPLACE VIEW public.vw_option_dependencies AS
SELECT 
    od.id,
    od.option_id,
    p1.model_number as option_model,
    p1.product_type as option_type,
    od.depends_on_option_id,
    p2.model_number as depends_on_model,
    p2.product_type as depends_on_type,
    od.dependency_type,
    od.notes,
    od.created_at,
    od.updated_at
FROM krai_core.option_dependencies od
LEFT JOIN krai_core.products p1 ON p1.id = od.option_id
LEFT JOIN krai_core.products p2 ON p2.id = od.depends_on_option_id;

-- Grant access to view
GRANT SELECT ON public.vw_option_dependencies TO authenticated, anon, service_role;

-- Add comments
COMMENT ON TABLE krai_core.option_dependencies IS 'Models complex relationships between product options/accessories';
COMMENT ON COLUMN krai_core.option_dependencies.dependency_type IS 'Type: requires (needs), excludes (conflicts), alternative (or)';
COMMENT ON VIEW public.vw_option_dependencies IS 'Easy-to-query view of option dependencies with product details';

-- Example data (commented out - for reference only)
/*
-- Finisher FS-533 requires Paper Tray PF-707
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
VALUES (
    (SELECT id FROM krai_core.products WHERE model_number = 'FS-533'),
    (SELECT id FROM krai_core.products WHERE model_number = 'PF-707'),
    'requires',
    'Finisher requires paper tray for proper operation'
);

-- Large Capacity Tray excludes Standard Tray
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
VALUES (
    (SELECT id FROM krai_core.products WHERE model_number = 'LCT-100'),
    (SELECT id FROM krai_core.products WHERE model_number = 'STD-TRAY'),
    'excludes',
    'Cannot install both large capacity and standard tray'
);

-- Finisher FS-533 OR FS-534 (alternatives)
INSERT INTO krai_core.option_dependencies (option_id, depends_on_option_id, dependency_type, notes)
VALUES (
    (SELECT id FROM krai_core.products WHERE model_number = 'FS-533'),
    (SELECT id FROM krai_core.products WHERE model_number = 'FS-534'),
    'alternative',
    'Choose either FS-533 or FS-534, not both'
);
*/
