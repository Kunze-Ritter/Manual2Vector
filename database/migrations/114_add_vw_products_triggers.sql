-- Migration 114: Add INSTEAD OF triggers for vw_products
-- ======================================================================
-- Description: Enable INSERT/UPDATE/DELETE on vw_products view
-- Date: 2025-10-23
-- Reason: PostgREST can only access public schema, views with JOINs need triggers
-- ======================================================================

-- DROP existing triggers if any
DROP TRIGGER IF EXISTS vw_products_insert_trigger ON public.vw_products;
DROP TRIGGER IF EXISTS vw_products_update_trigger ON public.vw_products;
DROP TRIGGER IF EXISTS vw_products_delete_trigger ON public.vw_products;

-- DROP existing functions if any
DROP FUNCTION IF EXISTS public.vw_products_insert();
DROP FUNCTION IF EXISTS public.vw_products_update();
DROP FUNCTION IF EXISTS public.vw_products_delete();

-- ======================================================================
-- INSERT Trigger Function
-- ======================================================================
CREATE OR REPLACE FUNCTION public.vw_products_insert()
RETURNS TRIGGER AS $$
DECLARE
    new_id uuid;
BEGIN
    IF NEW.product_type IS NULL THEN
        RAISE EXCEPTION 'product_type must be provided when inserting via vw_products view.';
    END IF;

    new_id := COALESCE(NEW.id, uuid_generate_v4());

    INSERT INTO krai_core.products (
        id,
        manufacturer_id,
        series_id,
        model_number,
        product_type,
        specifications,
        pricing,
        lifecycle,
        urls,
        metadata,
        oem_manufacturer,
        oem_relationship_type,
        oem_notes
    ) VALUES (
        new_id,
        NEW.manufacturer_id,
        NEW.series_id,
        NEW.model_number,
        NEW.product_type,
        COALESCE(NEW.specifications, '{}'::jsonb),
        COALESCE(NEW.pricing, '{}'::jsonb),
        COALESCE(NEW.lifecycle, '{}'::jsonb),
        COALESCE(NEW.urls, '{}'::jsonb),
        COALESCE(NEW.metadata, '{}'::jsonb),
        NEW.oem_manufacturer,
        NEW.oem_relationship_type,
        NEW.oem_notes
    );
    NEW.id := new_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ======================================================================
-- UPDATE Trigger Function
-- ======================================================================
CREATE OR REPLACE FUNCTION public.vw_products_update()
RETURNS TRIGGER AS $$
DECLARE
    target_product_type text;
BEGIN
    target_product_type := COALESCE(NEW.product_type, OLD.product_type);

    IF target_product_type IS NULL THEN
        RAISE EXCEPTION 'product_type must be provided when updating via vw_products view.';
    END IF;

    UPDATE krai_core.products
    SET
        manufacturer_id = NEW.manufacturer_id,
        series_id = NEW.series_id,
        model_number = NEW.model_number,
        product_type = target_product_type,
        specifications = NEW.specifications,
        pricing = NEW.pricing,
        lifecycle = NEW.lifecycle,
        urls = NEW.urls,
        metadata = NEW.metadata,
        oem_manufacturer = NEW.oem_manufacturer,
        oem_relationship_type = NEW.oem_relationship_type,
        oem_notes = NEW.oem_notes,
        updated_at = NOW()
    WHERE id = OLD.id;

    NEW.product_type := target_product_type;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ======================================================================
-- DELETE Trigger Function
-- ======================================================================
CREATE OR REPLACE FUNCTION public.vw_products_delete()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM krai_core.products
    WHERE id = OLD.id;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- ======================================================================
-- Create INSTEAD OF Triggers
-- ======================================================================
CREATE TRIGGER vw_products_insert_trigger
    INSTEAD OF INSERT ON public.vw_products
    FOR EACH ROW
    EXECUTE FUNCTION public.vw_products_insert();

CREATE TRIGGER vw_products_update_trigger
    INSTEAD OF UPDATE ON public.vw_products
    FOR EACH ROW
    EXECUTE FUNCTION public.vw_products_update();

CREATE TRIGGER vw_products_delete_trigger
    INSTEAD OF DELETE ON public.vw_products
    FOR EACH ROW
    EXECUTE FUNCTION public.vw_products_delete();

-- ======================================================================
-- Grant permissions
-- ======================================================================
GRANT EXECUTE ON FUNCTION public.vw_products_insert() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.vw_products_update() TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.vw_products_delete() TO anon, authenticated, service_role;

-- ======================================================================
-- Test the triggers
-- ======================================================================
-- Test INSERT (should work now)
-- INSERT INTO public.vw_products (model_number, manufacturer_id, product_type)
-- VALUES ('TEST-123', (SELECT id FROM krai_core.manufacturers LIMIT 1), 'printer');
-- 
-- Test UPDATE (should work now)
-- UPDATE public.vw_products SET product_type = 'laser_multifunction' WHERE model_number = 'TEST-123';
--
-- Test DELETE (should work now)
-- DELETE FROM public.vw_products WHERE model_number = 'TEST-123';
