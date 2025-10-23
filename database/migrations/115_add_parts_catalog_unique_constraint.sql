-- Ensure parts_catalog upserts have a matching unique constraint
ALTER TABLE krai_parts.parts_catalog
    ADD CONSTRAINT parts_catalog_manufacturer_part_unique
    UNIQUE (manufacturer_id, part_number);
