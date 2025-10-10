# Product Accessories Junction Table Guide

## Overview

The `product_accessories` table creates a **Many-to-Many (M:N)** relationship between products and their compatible accessories/options.

## Why M:N instead of parent_id?

**Old approach (removed):**
```sql
products.parent_id → 1:N relationship
Problem: One accessory can only have ONE parent product ❌
```

**New approach:**
```sql
product_accessories → M:N relationship
Solution: One accessory can fit MULTIPLE products ✅
```

## Schema

```sql
CREATE TABLE krai_core.product_accessories (
    id UUID PRIMARY KEY,
    product_id UUID,        -- Main product (e.g., bizhub C558)
    accessory_id UUID,      -- Accessory (e.g., Finisher FS-533)
    compatibility_notes TEXT,
    is_standard BOOLEAN,    -- Standard or optional?
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## Examples

### Example 1: Finisher for multiple models

```sql
-- Finisher FS-533 fits multiple bizhub models
INSERT INTO product_accessories (product_id, accessory_id, is_standard)
VALUES
    ('bizhub-c558-id', 'finisher-fs533-id', false),
    ('bizhub-c658-id', 'finisher-fs533-id', false),
    ('bizhub-c758-id', 'finisher-fs533-id', false);
```

### Example 2: Paper tray standard on some, optional on others

```sql
-- Paper Tray PF-707
INSERT INTO product_accessories (product_id, accessory_id, is_standard)
VALUES
    ('bizhub-c558-id', 'tray-pf707-id', true),   -- Standard
    ('bizhub-c458-id', 'tray-pf707-id', false);  -- Optional
```

## Queries

### Get all accessories for a product

```sql
SELECT 
    p.model_number AS accessory,
    pa.is_standard,
    pa.compatibility_notes
FROM product_accessories pa
JOIN products p ON p.id = pa.accessory_id
WHERE pa.product_id = 'bizhub-c558-id';
```

### Get all products that can use an accessory

```sql
SELECT 
    p.model_number AS product,
    pa.is_standard
FROM product_accessories pa
JOIN products p ON p.id = pa.product_id
WHERE pa.accessory_id = 'finisher-fs533-id';
```

### Find products with specific accessory as standard

```sql
SELECT p.model_number
FROM product_accessories pa
JOIN products p ON p.id = pa.product_id
WHERE pa.accessory_id = 'tray-pf707-id'
  AND pa.is_standard = true;
```

## Benefits

✅ **Accurate modeling:** One accessory → many products  
✅ **Flexible:** Track standard vs optional accessories  
✅ **Queryable:** Easy to find compatible products/accessories  
✅ **Scalable:** No limit on accessory-product combinations  

## Migration

Applied in: `72_remove_parent_id_add_accessories_junction.sql`

- ✅ Removed `parent_id` from products
- ✅ Created `product_accessories` junction table
- ✅ Added indexes for performance
- ✅ Added constraints (unique, no self-reference)
