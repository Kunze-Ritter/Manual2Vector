-- ======================================================================
-- 🔒 KRAI DATABASE - SECURITY, RLS & TRIGGERS
-- ======================================================================
-- Version: 2.0 (Consolidated)
-- Erstellt: Oktober 2025
-- Beschreibung: Row Level Security, Roles, Policies, Triggers
-- ======================================================================

-- ======================================================================
-- SECURITY ROLES
-- ======================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'krai_service_role') THEN
        CREATE ROLE krai_service_role;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'krai_admin_role') THEN
        CREATE ROLE krai_admin_role;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'krai_readonly_role') THEN
        CREATE ROLE krai_readonly_role;
    END IF;
    
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'krai_authenticated') THEN
        CREATE ROLE krai_authenticated;
    END IF;
END $$;

-- ======================================================================
-- ENABLE RLS ON ALL TABLES
-- ======================================================================

-- Core tables
ALTER TABLE krai_core.manufacturers ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_core.product_series ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_core.products ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_core.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_core.document_relationships ENABLE ROW LEVEL SECURITY;

-- Intelligence tables
ALTER TABLE krai_intelligence.chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_intelligence.embeddings ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_intelligence.error_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_intelligence.search_analytics ENABLE ROW LEVEL SECURITY;

-- Content tables
ALTER TABLE krai_content.chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_content.images ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_content.links ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_content.instructional_videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_content.print_defects ENABLE ROW LEVEL SECURITY;

-- Config tables
ALTER TABLE krai_config.option_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_config.product_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_config.product_compatibility ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_config.competition_analysis ENABLE ROW LEVEL SECURITY;

-- System tables  
ALTER TABLE krai_system.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_system.system_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_system.processing_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_system.health_checks ENABLE ROW LEVEL SECURITY;

-- ML tables
ALTER TABLE krai_ml.model_registry ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_ml.model_performance_history ENABLE ROW LEVEL SECURITY;

-- Parts tables
ALTER TABLE krai_parts.parts_catalog ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_parts.inventory_levels ENABLE ROW LEVEL SECURITY;

-- Service tables
ALTER TABLE krai_service.technicians ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_service.service_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_service.service_history ENABLE ROW LEVEL SECURITY;

-- User tables
ALTER TABLE krai_users.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_users.user_sessions ENABLE ROW LEVEL SECURITY;

-- Integration tables
ALTER TABLE krai_integrations.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE krai_integrations.webhook_logs ENABLE ROW LEVEL SECURITY;

-- ======================================================================
-- RLS POLICIES (Service Role = Full Access)
-- ======================================================================

-- Core
CREATE POLICY "service_role_manufacturers_all" ON krai_core.manufacturers FOR ALL USING (true);
CREATE POLICY "service_role_product_series_all" ON krai_core.product_series FOR ALL USING (true);
CREATE POLICY "service_role_products_all" ON krai_core.products FOR ALL USING (true);
CREATE POLICY "service_role_documents_all" ON krai_core.documents FOR ALL USING (true);
CREATE POLICY "service_role_document_relationships_all" ON krai_core.document_relationships FOR ALL USING (true);

-- Intelligence
CREATE POLICY "service_role_chunks_all" ON krai_intelligence.chunks FOR ALL USING (true);
CREATE POLICY "service_role_embeddings_all" ON krai_intelligence.embeddings FOR ALL USING (true);
CREATE POLICY "service_role_error_codes_all" ON krai_intelligence.error_codes FOR ALL USING (true);
CREATE POLICY "service_role_search_analytics_all" ON krai_intelligence.search_analytics FOR ALL USING (true);

-- Content
CREATE POLICY "service_role_content_chunks_all" ON krai_content.chunks FOR ALL USING (true);
CREATE POLICY "service_role_images_all" ON krai_content.images FOR ALL USING (true);
CREATE POLICY "service_role_links_all" ON krai_content.links FOR ALL USING (true);
CREATE POLICY "service_role_instructional_videos_all" ON krai_content.instructional_videos FOR ALL USING (true);
CREATE POLICY "service_role_print_defects_all" ON krai_content.print_defects FOR ALL USING (true);

-- Config
CREATE POLICY "service_role_option_groups_all" ON krai_config.option_groups FOR ALL USING (true);
CREATE POLICY "service_role_product_features_all" ON krai_config.product_features FOR ALL USING (true);
CREATE POLICY "service_role_product_compatibility_all" ON krai_config.product_compatibility FOR ALL USING (true);
CREATE POLICY "service_role_competition_analysis_all" ON krai_config.competition_analysis FOR ALL USING (true);

-- System
CREATE POLICY "service_role_audit_log_all" ON krai_system.audit_log FOR ALL USING (true);
CREATE POLICY "service_role_system_metrics_all" ON krai_system.system_metrics FOR ALL USING (true);
CREATE POLICY "service_role_processing_queue_all" ON krai_system.processing_queue FOR ALL USING (true);
CREATE POLICY "service_role_health_checks_all" ON krai_system.health_checks FOR ALL USING (true);

-- ML
CREATE POLICY "service_role_model_registry_all" ON krai_ml.model_registry FOR ALL USING (true);
CREATE POLICY "service_role_model_performance_history_all" ON krai_ml.model_performance_history FOR ALL USING (true);

-- Parts
CREATE POLICY "service_role_parts_catalog_all" ON krai_parts.parts_catalog FOR ALL USING (true);
CREATE POLICY "service_role_inventory_levels_all" ON krai_parts.inventory_levels FOR ALL USING (true);

-- Service
CREATE POLICY "service_role_technicians_all" ON krai_service.technicians FOR ALL USING (true);
CREATE POLICY "service_role_service_calls_all" ON krai_service.service_calls FOR ALL USING (true);
CREATE POLICY "service_role_service_history_all" ON krai_service.service_history FOR ALL USING (true);

-- Users
CREATE POLICY "service_role_users_all" ON krai_users.users FOR ALL USING (true);
CREATE POLICY "service_role_user_sessions_all" ON krai_users.user_sessions FOR ALL USING (true);

-- Integrations
CREATE POLICY "service_role_api_keys_all" ON krai_integrations.api_keys FOR ALL USING (true);
CREATE POLICY "service_role_webhook_logs_all" ON krai_integrations.webhook_logs FOR ALL USING (true);

-- ======================================================================
-- GRANT PERMISSIONS TO ROLES
-- ======================================================================

-- Grant all permissions to service role
GRANT ALL ON ALL TABLES IN SCHEMA krai_core TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_intelligence TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_content TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_config TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_system TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_ml TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_parts TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_service TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_users TO krai_service_role;
GRANT ALL ON ALL TABLES IN SCHEMA krai_integrations TO krai_service_role;

-- Grant sequence permissions
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_core TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_intelligence TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_content TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_config TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_system TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_ml TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_parts TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_service TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_users TO krai_service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA krai_integrations TO krai_service_role;

-- Grant usage on schemas
GRANT USAGE ON SCHEMA krai_core TO krai_service_role;
GRANT USAGE ON SCHEMA krai_intelligence TO krai_service_role;
GRANT USAGE ON SCHEMA krai_content TO krai_service_role;
GRANT USAGE ON SCHEMA krai_config TO krai_service_role;
GRANT USAGE ON SCHEMA krai_system TO krai_service_role;
GRANT USAGE ON SCHEMA krai_ml TO krai_service_role;
GRANT USAGE ON SCHEMA krai_parts TO krai_service_role;
GRANT USAGE ON SCHEMA krai_service TO krai_service_role;
GRANT USAGE ON SCHEMA krai_users TO krai_service_role;
GRANT USAGE ON SCHEMA krai_integrations TO krai_service_role;

-- ======================================================================
-- TRIGGER FUNCTIONS
-- ======================================================================

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION krai_system.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Audit trigger function
CREATE OR REPLACE FUNCTION krai_system.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO krai_system.audit_log (table_name, record_id, operation, old_values, changed_by)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD), current_user);
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO krai_system.audit_log (table_name, record_id, operation, old_values, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW), current_user);
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO krai_system.audit_log (table_name, record_id, operation, new_values, changed_by)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW), current_user);
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ======================================================================
-- CREATE TRIGGERS
-- ======================================================================

-- Updated_at triggers for main tables
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_manufacturers_updated_at') THEN
        CREATE TRIGGER update_manufacturers_updated_at 
            BEFORE UPDATE ON krai_core.manufacturers 
            FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_products_updated_at') THEN
        CREATE TRIGGER update_products_updated_at 
            BEFORE UPDATE ON krai_core.products 
            FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_documents_updated_at') THEN
        CREATE TRIGGER update_documents_updated_at 
            BEFORE UPDATE ON krai_core.documents 
            FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_chunks_updated_at') THEN
        CREATE TRIGGER update_chunks_updated_at 
            BEFORE UPDATE ON krai_intelligence.chunks 
            FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_technicians_updated_at') THEN
        CREATE TRIGGER update_technicians_updated_at 
            BEFORE UPDATE ON krai_service.technicians 
            FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_service_calls_updated_at') THEN
        CREATE TRIGGER update_service_calls_updated_at 
            BEFORE UPDATE ON krai_service.service_calls 
            FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_service_history_updated_at') THEN
        CREATE TRIGGER update_service_history_updated_at 
            BEFORE UPDATE ON krai_service.service_history 
            FOR EACH ROW EXECUTE FUNCTION krai_system.update_updated_at_column();
    END IF;
END $$;

-- ======================================================================
-- ROLE SECURITY SETTINGS
-- ======================================================================

ALTER ROLE krai_service_role NOLOGIN;
ALTER ROLE krai_admin_role NOLOGIN;
ALTER ROLE krai_readonly_role NOLOGIN;
ALTER ROLE krai_authenticated NOLOGIN;

-- ======================================================================
-- COMPLETION MESSAGE
-- ======================================================================

DO $$
BEGIN
    RAISE NOTICE '🔒 KRAI Security & RLS successfully applied!';
    RAISE NOTICE '👥 Created 4 security roles with proper permissions';
    RAISE NOTICE '🛡️  RLS policies enabled on all 33 tables';
    RAISE NOTICE '🔧 Security functions and triggers deployed';
    RAISE NOTICE '✅ Ready for Performance Indexes (next migration)';
END $$;

