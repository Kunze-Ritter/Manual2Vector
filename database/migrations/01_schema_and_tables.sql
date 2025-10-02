-- ======================================================================
-- 🚀 KRAI DATABASE - COMPLETE SCHEMA & TABLES
-- ======================================================================
-- Version: 2.0 (Consolidated)
-- Erstellt: Oktober 2025
-- Beschreibung: Alle Tabellen, Foreign Keys, Extensions
-- ======================================================================

-- ======================================================================
-- EXTENSIONS
-- ======================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "pg_trgm" WITH SCHEMA extensions; 
CREATE EXTENSION IF NOT EXISTS "unaccent" WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "vector" WITH SCHEMA extensions;

-- Performance Analysis Extensions
CREATE EXTENSION IF NOT EXISTS "hypopg" WITH SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "index_advisor" WITH SCHEMA extensions;

-- Public wrapper function for UUID generation
CREATE OR REPLACE FUNCTION uuid_generate_v4() 
RETURNS uuid AS 'SELECT extensions.uuid_generate_v4()' 
LANGUAGE SQL IMMUTABLE;

-- ======================================================================
-- SCHEMAS
-- ======================================================================

CREATE SCHEMA IF NOT EXISTS krai_core;
CREATE SCHEMA IF NOT EXISTS krai_intelligence; 
CREATE SCHEMA IF NOT EXISTS krai_content;
CREATE SCHEMA IF NOT EXISTS krai_config;
CREATE SCHEMA IF NOT EXISTS krai_system;
CREATE SCHEMA IF NOT EXISTS krai_ml;
CREATE SCHEMA IF NOT EXISTS krai_parts;
CREATE SCHEMA IF NOT EXISTS krai_service;
CREATE SCHEMA IF NOT EXISTS krai_users;
CREATE SCHEMA IF NOT EXISTS krai_integrations;

COMMENT ON SCHEMA krai_core IS 'Core business entities: manufacturers, products, documents';
COMMENT ON SCHEMA krai_intelligence IS 'AI/ML intelligence: chunks, embeddings, analytics';
COMMENT ON SCHEMA krai_content IS 'Media content: images, videos, defect patterns';
COMMENT ON SCHEMA krai_config IS 'Configuration: features, options, compatibility';
COMMENT ON SCHEMA krai_system IS 'System operations: audit, queue, health monitoring';
COMMENT ON SCHEMA krai_ml IS 'Machine learning models and training data';
COMMENT ON SCHEMA krai_parts IS 'Parts catalog and inventory management';
COMMENT ON SCHEMA krai_service IS 'Service management and technician workflows';
COMMENT ON SCHEMA krai_users IS 'User management and access control';
COMMENT ON SCHEMA krai_integrations IS 'External system integrations and APIs';

-- ======================================================================
-- KRAI_CORE TABLES
-- ======================================================================

-- Manufacturers
CREATE TABLE IF NOT EXISTS krai_core.manufacturers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    short_name VARCHAR(10),
    country VARCHAR(50),
    founded_year INTEGER,
    website VARCHAR(255),
    support_email VARCHAR(255),
    support_phone VARCHAR(50),
    logo_url TEXT,
    is_competitor BOOLEAN DEFAULT false,
    market_share_percent DECIMAL(5,2),
    annual_revenue_usd BIGINT,
    employee_count INTEGER,
    headquarters_address TEXT,
    stock_symbol VARCHAR(10),
    primary_business_segment VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Product Series
CREATE TABLE IF NOT EXISTS krai_core.product_series (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    series_name VARCHAR(100) NOT NULL,
    series_code VARCHAR(50),
    launch_date DATE,
    end_of_life_date DATE,
    target_market VARCHAR(100),
    price_range VARCHAR(50),
    key_features JSONB DEFAULT '{}',
    series_description TEXT,
    marketing_name VARCHAR(150),
    successor_series_id UUID REFERENCES krai_core.product_series(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(manufacturer_id, series_name)
);

-- Products
CREATE TABLE IF NOT EXISTS krai_core.products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_id UUID REFERENCES krai_core.products(id),
    manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    series_id UUID REFERENCES krai_core.product_series(id),
    model_number VARCHAR(100) NOT NULL,
    model_name VARCHAR(200),
    product_type VARCHAR(50) NOT NULL DEFAULT 'printer',
    launch_date DATE,
    end_of_life_date DATE,
    msrp_usd DECIMAL(10,2),
    weight_kg DECIMAL(8,2),
    dimensions_mm JSONB,
    color_options TEXT[],
    connectivity_options TEXT[],
    print_technology VARCHAR(50),
    max_print_speed_ppm INTEGER,
    max_resolution_dpi INTEGER,
    max_paper_size VARCHAR(20),
    duplex_capable BOOLEAN DEFAULT false,
    network_capable BOOLEAN DEFAULT false,
    mobile_print_support BOOLEAN DEFAULT false,
    supported_languages TEXT[],
    energy_star_certified BOOLEAN DEFAULT false,
    warranty_months INTEGER DEFAULT 12,
    service_manual_url TEXT,
    parts_catalog_url TEXT,
    driver_download_url TEXT,
    firmware_version VARCHAR(50),
    option_dependencies JSONB DEFAULT '{}',
    replacement_parts JSONB DEFAULT '{}',
    common_issues JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Documents
CREATE TABLE IF NOT EXISTS krai_core.documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID REFERENCES krai_core.manufacturers(id),
    product_id UUID REFERENCES krai_core.products(id),
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size BIGINT,
    file_hash VARCHAR(64),
    storage_path TEXT,
    storage_url TEXT,
    document_type VARCHAR(100),
    language VARCHAR(10) DEFAULT 'en',
    version VARCHAR(50),
    publish_date DATE,
    page_count INTEGER,
    word_count INTEGER,
    character_count INTEGER,
    content_text TEXT,
    content_summary TEXT,
    extracted_metadata JSONB DEFAULT '{}',
    processing_status VARCHAR(50) DEFAULT 'pending',
    confidence_score DECIMAL(3,2),
    manual_review_required BOOLEAN DEFAULT false,
    manual_review_completed BOOLEAN DEFAULT false,
    manual_review_notes TEXT,
    ocr_confidence DECIMAL(3,2),
    manufacturer VARCHAR(100),
    series VARCHAR(100),
    models TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document Relationships
CREATE TABLE IF NOT EXISTS krai_core.document_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    primary_document_id UUID NOT NULL REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    secondary_document_id UUID NOT NULL REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL,
    relationship_strength DECIMAL(3,2) DEFAULT 0.5,
    auto_discovered BOOLEAN DEFAULT true,
    manual_verification BOOLEAN DEFAULT false,
    verification_date TIMESTAMP WITH TIME ZONE,
    verified_by VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(primary_document_id, secondary_document_id, relationship_type)
);

-- ======================================================================
-- KRAI_INTELLIGENCE TABLES
-- ======================================================================

-- Chunks
CREATE TABLE IF NOT EXISTS krai_intelligence.chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    text_chunk TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    page_start INTEGER,
    page_end INTEGER,
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (processing_status IN ('pending', 'completed', 'failed')),
    fingerprint VARCHAR(32) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Embeddings
CREATE TABLE IF NOT EXISTS krai_intelligence.embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID NOT NULL REFERENCES krai_intelligence.chunks(id) ON DELETE CASCADE,
    embedding extensions.vector(768),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) DEFAULT 'latest',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Error Codes
CREATE TABLE IF NOT EXISTS krai_intelligence.error_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    chunk_id UUID REFERENCES krai_intelligence.chunks(id) ON DELETE CASCADE,
    document_id UUID REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    manufacturer_id UUID REFERENCES krai_core.manufacturers(id),
    error_code VARCHAR(20) NOT NULL,
    error_description TEXT,
    solution_text TEXT,
    page_number INTEGER,
    confidence_score DECIMAL(3,2),
    extraction_method VARCHAR(50),
    requires_technician BOOLEAN DEFAULT false,
    requires_parts BOOLEAN DEFAULT false,
    estimated_fix_time_minutes INTEGER,
    severity_level VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Search Analytics
CREATE TABLE IF NOT EXISTS krai_intelligence.search_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_query TEXT NOT NULL,
    search_type VARCHAR(50),
    results_count INTEGER,
    click_through_rate DECIMAL(5,4),
    user_satisfaction_rating INTEGER CHECK (user_satisfaction_rating >= 1 AND user_satisfaction_rating <= 5),
    search_duration_ms INTEGER,
    result_relevance_scores JSONB,
    user_session_id VARCHAR(100),
    user_id UUID,
    manufacturer_filter UUID REFERENCES krai_core.manufacturers(id),
    product_filter UUID REFERENCES krai_core.products(id),
    document_type_filter VARCHAR(100),
    language_filter VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_CONTENT TABLES
-- ======================================================================

-- Content Chunks
CREATE TABLE IF NOT EXISTS krai_content.chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_type VARCHAR(50) DEFAULT 'text',
    chunk_index INTEGER NOT NULL,
    page_number INTEGER,
    section_title VARCHAR(255),
    confidence_score DECIMAL(3,2),
    language VARCHAR(10) DEFAULT 'en',
    processing_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Images
CREATE TABLE IF NOT EXISTS krai_content.images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES krai_content.chunks(id),
    filename VARCHAR(255),
    original_filename VARCHAR(255),
    storage_path TEXT,
    storage_url TEXT NOT NULL,
    file_size INTEGER,
    image_format VARCHAR(10),
    width_px INTEGER,
    height_px INTEGER,
    page_number INTEGER,
    image_index INTEGER,
    image_type VARCHAR(50),
    ai_description TEXT,
    ai_confidence DECIMAL(3,2),
    contains_text BOOLEAN DEFAULT false,
    ocr_text TEXT,
    ocr_confidence DECIMAL(3,2),
    manual_description TEXT,
    tags TEXT[],
    file_hash VARCHAR(64),
    figure_number VARCHAR(50),
    figure_context TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Links (NEU)
CREATE TABLE IF NOT EXISTS krai_content.links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES krai_core.documents(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    link_type VARCHAR(50) NOT NULL DEFAULT 'external',
    page_number INTEGER NOT NULL,
    description TEXT,
    position_data JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE krai_content.links IS 'External links extracted from PDFs (videos, tutorials, etc.)';
COMMENT ON COLUMN krai_content.links.link_type IS 'Type: video, external, tutorial';
COMMENT ON COLUMN krai_content.images.figure_number IS 'Figure reference number (e.g., "1", "2.1")';
COMMENT ON COLUMN krai_content.images.figure_context IS 'Context text around figure reference';

-- Instructional Videos
CREATE TABLE IF NOT EXISTS krai_content.instructional_videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    video_url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration_seconds INTEGER,
    file_size_mb INTEGER,
    video_format VARCHAR(20),
    resolution VARCHAR(20),
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Print Defects
CREATE TABLE IF NOT EXISTS krai_content.print_defects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    product_id UUID REFERENCES krai_core.products(id),
    original_image_id UUID REFERENCES krai_content.images(id),
    defect_name VARCHAR(100) NOT NULL,
    defect_category VARCHAR(50),
    defect_description TEXT,
    example_image_url TEXT,
    annotated_image_url TEXT,
    detection_confidence DECIMAL(3,2),
    common_causes JSONB DEFAULT '[]',
    recommended_solutions JSONB DEFAULT '[]',
    related_error_codes TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_CONFIG TABLES
-- ======================================================================

-- Option Groups
CREATE TABLE IF NOT EXISTS krai_config.option_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    group_name VARCHAR(100) NOT NULL,
    group_description TEXT,
    display_order INTEGER DEFAULT 0,
    is_required BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(manufacturer_id, group_name)
);

-- Product Features
CREATE TABLE IF NOT EXISTS krai_config.product_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES krai_core.products(id) ON DELETE CASCADE,
    feature_id UUID NOT NULL REFERENCES krai_config.option_groups(id),
    feature_value TEXT,
    is_standard BOOLEAN DEFAULT true,
    additional_cost_usd DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(product_id, feature_id)
);

-- Product Compatibility
CREATE TABLE IF NOT EXISTS krai_config.product_compatibility (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    base_product_id UUID NOT NULL REFERENCES krai_core.products(id),
    option_product_id UUID NOT NULL REFERENCES krai_core.products(id),
    compatibility_type VARCHAR(50) DEFAULT 'compatible',
    compatibility_notes TEXT,
    validated_date DATE,
    validation_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(base_product_id, option_product_id)
);

-- Competition Analysis
CREATE TABLE IF NOT EXISTS krai_config.competition_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    our_product_id UUID NOT NULL REFERENCES krai_core.products(id),
    competitor_manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    competitor_model_name VARCHAR(200),
    comparison_category VARCHAR(100),
    our_advantage TEXT,
    competitor_advantage TEXT,
    feature_comparison JSONB DEFAULT '{}',
    price_comparison JSONB DEFAULT '{}',
    market_position VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_SYSTEM TABLES
-- ======================================================================

-- Audit Log
CREATE TABLE IF NOT EXISTS krai_system.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    record_id UUID NOT NULL,
    operation VARCHAR(10) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_values JSONB,
    new_values JSONB,
    changed_by VARCHAR(100),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id VARCHAR(100),
    ip_address INET,
    user_agent TEXT
);

-- System Metrics
CREATE TABLE IF NOT EXISTS krai_system.system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6),
    metric_unit VARCHAR(20),
    metric_category VARCHAR(50),
    collection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    server_instance VARCHAR(100),
    additional_context JSONB DEFAULT '{}'
);

-- Processing Queue
CREATE TABLE IF NOT EXISTS krai_system.processing_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES krai_core.documents(id),
    chunk_id UUID REFERENCES krai_intelligence.chunks(id),
    image_id UUID REFERENCES krai_content.images(id),
    video_id UUID REFERENCES krai_content.instructional_videos(id),
    task_type VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'pending',
    scheduled_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Health Checks
CREATE TABLE IF NOT EXISTS krai_system.health_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    details JSONB DEFAULT '{}',
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_ML TABLES
-- ======================================================================

CREATE TABLE IF NOT EXISTS krai_ml.model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL UNIQUE,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    framework VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS krai_ml.model_performance_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES krai_ml.model_registry(id),
    accuracy_score DECIMAL(5,4),
    precision_score DECIMAL(5,4),
    recall_score DECIMAL(5,4),
    f1_score DECIMAL(5,4),
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_PARTS TABLES
-- ======================================================================

CREATE TABLE IF NOT EXISTS krai_parts.parts_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    part_number VARCHAR(100) NOT NULL,
    part_name VARCHAR(255),
    part_description TEXT,
    part_category VARCHAR(100),
    unit_price_usd DECIMAL(10,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS krai_parts.inventory_levels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    part_id UUID NOT NULL REFERENCES krai_parts.parts_catalog(id),
    warehouse_location VARCHAR(100),
    current_stock INTEGER DEFAULT 0,
    minimum_stock_level INTEGER DEFAULT 0,
    maximum_stock_level INTEGER DEFAULT 1000,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_USERS TABLES (müssen VOR krai_service existieren!)
-- ======================================================================

CREATE TABLE IF NOT EXISTS krai_users.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    preferred_manufacturer_id UUID REFERENCES krai_core.manufacturers(id),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS krai_users.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES krai_users.users(id),
    session_token VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_SERVICE TABLES (NACH krai_users!)
-- ======================================================================

-- Technicians (NEU - keine Abhängigkeiten)
CREATE TABLE IF NOT EXISTS krai_service.technicians (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
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

-- Service Calls
CREATE TABLE IF NOT EXISTS krai_service.service_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    manufacturer_id UUID NOT NULL REFERENCES krai_core.manufacturers(id),
    product_id UUID REFERENCES krai_core.products(id),
    assigned_technician_id UUID REFERENCES krai_service.technicians(id),
    call_status VARCHAR(50) DEFAULT 'open',
    priority_level INTEGER DEFAULT 3,
    customer_name VARCHAR(255),
    customer_contact TEXT,
    issue_description TEXT,
    scheduled_date TIMESTAMP WITH TIME ZONE,
    completed_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Service History
CREATE TABLE IF NOT EXISTS krai_service.service_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_call_id UUID REFERENCES krai_service.service_calls(id) ON DELETE CASCADE,
    performed_by UUID REFERENCES krai_service.technicians(id),
    service_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    service_notes TEXT,
    parts_used JSONB DEFAULT '[]',
    labor_hours DECIMAL(4,2),
    service_type VARCHAR(50),
    outcome VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- KRAI_INTEGRATIONS TABLES
-- ======================================================================

CREATE TABLE IF NOT EXISTS krai_integrations.api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_name VARCHAR(100) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS krai_integrations.webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_url TEXT NOT NULL,
    request_payload JSONB,
    response_status INTEGER,
    response_body TEXT,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ======================================================================
-- FOREIGN KEY CONSTRAINTS (nach allen Tabellen!)
-- ======================================================================

-- Technicians → Users (jetzt können wir es sicher hinzufügen)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'fk_technicians_user_id'
    ) THEN
        ALTER TABLE krai_service.technicians 
        ADD CONSTRAINT fk_technicians_user_id 
        FOREIGN KEY (user_id) REFERENCES krai_users.users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- ======================================================================
-- VIEWS
-- ======================================================================

-- Document Media Context View
CREATE OR REPLACE VIEW krai_content.document_media_context AS
SELECT 
    d.id as document_id,
    d.filename,
    d.manufacturer,
    d.document_type,
    i.id as image_id,
    i.filename as image_filename,
    i.figure_number,
    i.figure_context,
    i.page_number as image_page,
    i.storage_url as image_url,
    l.id as link_id,
    l.url as link_url,
    l.link_type,
    l.page_number as link_page,
    l.description as link_description
FROM krai_core.documents d
LEFT JOIN krai_content.images i ON d.id = i.document_id
LEFT JOIN krai_content.links l ON d.id = l.document_id
WHERE (i.id IS NOT NULL OR l.id IS NOT NULL);

COMMENT ON VIEW krai_content.document_media_context IS 'Unified view for agent context: documents with images, figures, and links';

-- Public Products View
CREATE OR REPLACE VIEW krai_core.public_products AS
SELECT 
    id,
    manufacturer_id,
    series_id,
    model_number,
    model_name,
    product_type,
    launch_date,
    print_technology,
    max_print_speed_ppm,
    max_resolution_dpi,
    created_at
FROM krai_core.products
WHERE end_of_life_date IS NULL OR end_of_life_date > CURRENT_DATE;

COMMENT ON VIEW krai_core.public_products IS 'Public view of products with non-sensitive information only';

-- ======================================================================
-- COMPLETION MESSAGE
-- ======================================================================

DO $$
BEGIN
    RAISE NOTICE '🎉 KRAI Complete Schema successfully created!';
    RAISE NOTICE '📊 Created 10 schemas with 33 tables';
    RAISE NOTICE '🔗 All foreign keys configured';
    RAISE NOTICE '👁️  Views created';
    RAISE NOTICE '⚡ Ready for RLS and Indexes (separate migrations)';
END $$;

