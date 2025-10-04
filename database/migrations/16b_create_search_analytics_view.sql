-- ============================================
-- Migration: Create search_analytics view for n8n
-- Date: 2025-10-02
-- Purpose: Allow n8n to log agent interactions for analytics
-- ============================================

-- View for n8n access
CREATE OR REPLACE VIEW public.vw_search_analytics AS
SELECT 
    id,
    search_query,
    search_type,
    results_count,
    click_through_rate,
    user_satisfaction_rating,
    search_duration_ms,
    result_relevance_scores,
    user_session_id,
    user_id,
    manufacturer_filter,
    product_filter,
    document_type_filter,
    language_filter,
    created_at
FROM krai_intelligence.search_analytics;

-- Grant permissions for n8n
GRANT SELECT, INSERT ON public.vw_search_analytics TO service_role;
GRANT SELECT ON public.vw_search_analytics TO authenticated;

-- INSTEAD OF INSERT Trigger (View kann nicht direkt INSERT)
CREATE OR REPLACE FUNCTION public.vw_search_analytics_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO krai_intelligence.search_analytics (
        search_query,
        search_type,
        results_count,
        user_satisfaction_rating,
        search_duration_ms,
        result_relevance_scores,
        user_session_id
    ) VALUES (
        NEW.search_query,
        COALESCE(NEW.search_type, 'agent_query'),
        COALESCE(NEW.results_count, 0),
        NEW.user_satisfaction_rating,
        NEW.search_duration_ms,
        COALESCE(NEW.result_relevance_scores, '{}'::jsonb),
        NEW.user_session_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER vw_search_analytics_insert_trigger
INSTEAD OF INSERT ON public.vw_search_analytics
FOR EACH ROW EXECUTE FUNCTION public.vw_search_analytics_insert();

COMMENT ON VIEW public.vw_search_analytics IS 'n8n-accessible view for logging agent interactions';

-- ============================================
-- VERIFICATION
-- ============================================
-- Test insert:
-- INSERT INTO public.vw_search_analytics (search_query, user_session_id, results_count)
-- VALUES ('Test query', 'test-session-123', 5);
--
-- Verify:
-- SELECT * FROM public.vw_search_analytics WHERE user_session_id = 'test-session-123';
--
-- Cleanup:
-- DELETE FROM krai_intelligence.search_analytics WHERE user_session_id = 'test-session-123';
-- ============================================
