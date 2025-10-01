-- ======================================================================
-- 🔧 KR-AI-ENGINE - FIX SERVICE SCHEMA
-- ======================================================================
-- This migration fixes the circular reference in krai_service schema
-- by adding a technicians table and updating foreign key constraints
-- ======================================================================

-- ======================================================================
-- STEP 1: DROP EXISTING CIRCULAR FOREIGN KEY CONSTRAINTS
-- ======================================================================

-- Drop the circular reference constraint
ALTER TABLE krai_service.service_calls 
DROP CONSTRAINT IF EXISTS fk_assigned_technician;

-- Drop the old performed_by constraint if exists
ALTER TABLE krai_service.service_history
DROP CONSTRAINT IF EXISTS fk_performed_by_user;

-- ======================================================================
-- STEP 2: CREATE TECHNICIANS TABLE
-- ======================================================================

CREATE TABLE IF NOT EXISTS krai_service.technicians (
    id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID,  -- Will be linked to krai_users.users later
    technician_name VARCHAR(255) NOT NULL,
    employee_id VARCHAR(50) UNIQUE,
    email VARCHAR(255),
    phone VARCHAR(50),
    certification_level VARCHAR(50),
    specializations TEXT[],
    is_active BOOLEAN DEFAULT true,
    hired_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- STEP 3: UPDATE SERVICE_HISTORY TABLE STRUCTURE
-- ======================================================================

-- Rename the column to match our schema (if different name exists)
DO $$
BEGIN
    -- Check if old column exists and rename it
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'krai_service' 
        AND table_name = 'service_history' 
        AND column_name = 'performed_by_user_id'
    ) THEN
        ALTER TABLE krai_service.service_history 
        RENAME COLUMN performed_by_user_id TO performed_by;
    END IF;
    
    -- Add columns if they don't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'krai_service' 
        AND table_name = 'service_history' 
        AND column_name = 'service_type'
    ) THEN
        ALTER TABLE krai_service.service_history 
        ADD COLUMN service_type VARCHAR(50),
        ADD COLUMN outcome VARCHAR(100),
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- ======================================================================
-- STEP 4: UPDATE SERVICE_CALLS TABLE STRUCTURE
-- ======================================================================

-- Add missing columns to service_calls
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'krai_service' 
        AND table_name = 'service_calls' 
        AND column_name = 'customer_name'
    ) THEN
        ALTER TABLE krai_service.service_calls 
        ADD COLUMN customer_name VARCHAR(255),
        ADD COLUMN customer_contact TEXT,
        ADD COLUMN issue_description TEXT,
        ADD COLUMN scheduled_date TIMESTAMP WITH TIME ZONE,
        ADD COLUMN completed_date TIMESTAMP WITH TIME ZONE,
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
    END IF;
END $$;

-- ======================================================================
-- STEP 5: ADD FOREIGN KEY CONSTRAINTS (CORRECT ORDER)
-- ======================================================================

-- Link technicians to users (if users table exists)
ALTER TABLE krai_service.technicians 
ADD CONSTRAINT fk_technicians_user_id 
FOREIGN KEY (user_id) REFERENCES krai_users.users(id) ON DELETE SET NULL;

-- Link service_calls to technicians (fix circular reference)
ALTER TABLE krai_service.service_calls
ADD CONSTRAINT fk_service_calls_technician
FOREIGN KEY (assigned_technician_id) REFERENCES krai_service.technicians(id) ON DELETE SET NULL;

-- Link service_history to technicians (instead of users)
ALTER TABLE krai_service.service_history
ADD CONSTRAINT fk_service_history_performed_by
FOREIGN KEY (performed_by) REFERENCES krai_service.technicians(id) ON DELETE SET NULL;

-- ======================================================================
-- STEP 6: ENABLE RLS ON NEW TABLE
-- ======================================================================

ALTER TABLE krai_service.technicians ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for technicians
CREATE POLICY "service_role_technicians_all" ON krai_service.technicians FOR ALL
    USING (true);

-- ======================================================================
-- STEP 7: CREATE INDEXES FOR PERFORMANCE
-- ======================================================================

CREATE INDEX IF NOT EXISTS idx_technicians_user_id 
    ON krai_service.technicians(user_id);

CREATE INDEX IF NOT EXISTS idx_technicians_employee_id 
    ON krai_service.technicians(employee_id);

CREATE INDEX IF NOT EXISTS idx_technicians_is_active 
    ON krai_service.technicians(is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_service_calls_assigned_technician_id 
    ON krai_service.service_calls(assigned_technician_id);

CREATE INDEX IF NOT EXISTS idx_service_calls_status 
    ON krai_service.service_calls(call_status);

CREATE INDEX IF NOT EXISTS idx_service_history_performed_by 
    ON krai_service.service_history(performed_by);

CREATE INDEX IF NOT EXISTS idx_service_history_service_date 
    ON krai_service.service_history(service_date DESC);

-- ======================================================================
-- STEP 8: CREATE UPDATE TRIGGER FOR TIMESTAMP
-- ======================================================================

-- Trigger for technicians
CREATE TRIGGER update_technicians_updated_at 
    BEFORE UPDATE ON krai_service.technicians 
    FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();

-- Trigger for service_calls
CREATE TRIGGER update_service_calls_updated_at 
    BEFORE UPDATE ON krai_service.service_calls 
    FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();

-- Trigger for service_history
CREATE TRIGGER update_service_history_updated_at 
    BEFORE UPDATE ON krai_service.service_history 
    FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();

-- ======================================================================
-- STEP 9: GRANT PERMISSIONS
-- ======================================================================

GRANT ALL ON krai_service.technicians TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_service TO krai_service_role;

-- ======================================================================
-- COMPLETION MESSAGE
-- ======================================================================

DO $$
BEGIN
    RAISE NOTICE '🔧 Service Schema Fix completed!';
    RAISE NOTICE '✅ Created technicians table';
    RAISE NOTICE '✅ Fixed circular foreign key reference';
    RAISE NOTICE '✅ Updated service_calls and service_history structure';
    RAISE NOTICE '✅ Added performance indexes';
    RAISE NOTICE '✅ Applied RLS policies';
    RAISE NOTICE '📊 Schema is now consistent with design';
END $$;

