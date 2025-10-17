"""
Generate Database Schema Documentation from Supabase
=====================================================
Uses the REAL column data from Supabase to create accurate documentation.
Paste the JSON result from the SQL query into this script.
"""

import json
from pathlib import Path
from datetime import datetime

def generate_doc():
    """Generate documentation from column data"""
    
    # Read JSON from file
    json_file = Path(__file__).parent / 'supabase_columns.json'
    
    if not json_file.exists():
        print(f"ERROR: {json_file} not found!")
        print("\n1. Führe in Supabase aus:")
        print("""
SELECT 
    c.table_schema,
    c.table_name,
    c.column_name,
    c.data_type,
    c.character_maximum_length,
    c.is_nullable,
    c.column_default,
    c.udt_name
FROM information_schema.columns c
WHERE c.table_schema LIKE 'krai_%'
ORDER BY c.table_schema, c.table_name, c.ordinal_position;
        """)
        print("\n2. Speichere das JSON-Ergebnis als 'supabase_columns.json' im scripts/ Ordner")
        return
    
    # Parse JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            columns = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not parse JSON: {e}")
        return
    
    # Group by schema and table
    tables = {}
    for col in columns:
        schema = col['table_schema']
        table = col['table_name']
        key = f"{schema}.{table}"
        
        if key not in tables:
            tables[key] = []
        
        tables[key].append(col)
    
    # Build documentation
    doc = []
    doc.append("# KRAI Database Schema Documentation")
    doc.append("=" * 80)
    doc.append("")
    doc.append(f"**Zuletzt aktualisiert:** {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}")
    doc.append("")
    doc.append("**Quelle:** Direkt aus Supabase (ECHTE Struktur)")
    doc.append("")
    doc.append("## ⚠️ WICHTIGE INFORMATIONEN")
    doc.append("")
    doc.append("### Embeddings Storage")
    doc.append("- **Embeddings sind in `krai_intelligence.chunks` als Spalte `embedding` gespeichert!**")
    doc.append("- Es gibt KEIN separates `krai_embeddings` Schema")
    doc.append("- Spalte: `embedding` (Typ: `vector(768)`)")
    doc.append("")
    doc.append("### View Naming Convention")
    doc.append("- Alle Views nutzen `vw_` Prefix")
    doc.append("- Views sind im `public` Schema")
    doc.append("- Tabellen sind in `krai_*` Schemas")
    doc.append("")
    doc.append("### Wichtige Tabellen für Processing")
    doc.append("- `krai_core.documents` - Haupttabelle für Dokumente")
    doc.append("- `krai_core.products` - Produkte")
    doc.append("- `krai_core.manufacturers` - Hersteller")
    doc.append("- `krai_intelligence.chunks` - Text-Chunks mit Embeddings")
    doc.append("- `krai_intelligence.error_codes` - Fehlercodes")
    doc.append("- `krai_content.videos` - Videos")
    doc.append("- `krai_content.links` - Links")
    doc.append("- `krai_content.images` - Bilder")
    doc.append("- `krai_parts.parts_catalog` - Ersatzteile")
    doc.append("")
    doc.append("---")
    doc.append("")
    doc.append("## Table of Contents")
    doc.append("")
    
    # Group by schema
    schemas = {}
    for table_key in sorted(tables.keys()):
        schema, table = table_key.split('.', 1)
        if schema not in schemas:
            schemas[schema] = []
        schemas[schema].append(table)
    
    # Add TOC
    for schema in sorted(schemas.keys()):
        doc.append(f"- [{schema}](#{schema.replace('_', '-')}) ({len(schemas[schema])} Tabellen)")
    
    doc.append("")
    doc.append("---")
    doc.append("")
    
    # Document each schema
    for schema in sorted(schemas.keys()):
        doc.append(f"## {schema}")
        doc.append("")
        
        for table in sorted(schemas[schema]):
            table_key = f"{schema}.{table}"
            doc.append(f"### {table_key}")
            doc.append("")
            
            cols = tables[table_key]
            
            doc.append("| Spalte | Typ | Nullable | Default |")
            doc.append("|--------|-----|----------|---------|")
            
            for col in cols:
                col_name = col['column_name']
                
                # Build type string
                data_type = col['data_type']
                if col['character_maximum_length']:
                    data_type = f"{data_type}({col['character_maximum_length']})"
                elif col['udt_name'] and col['udt_name'] != col['data_type']:
                    data_type = col['udt_name']
                
                # Nullable
                nullable = "YES" if col['is_nullable'] == 'YES' else "NO"
                
                # Default
                default = col['column_default'] or "-"
                if len(default) > 40:
                    default = default[:37] + "..."
                
                doc.append(f"| `{col_name}` | {data_type} | {nullable} | {default} |")
            
            doc.append("")
    
    # Add views section
    doc.append("---")
    doc.append("")
    doc.append("## Public Views (vw_*)")
    doc.append("")
    doc.append("Alle Views nutzen `vw_` Prefix und zeigen auf Tabellen in krai_* Schemas:")
    doc.append("")
    
    existing_views = [
        ("vw_agent_memory", "krai_agent.memory"),
        ("vw_audit_log", "krai_system.audit_log"),
        ("vw_chunks", "krai_intelligence.chunks", "⚠️ Enthält embedding Spalte!"),
        ("vw_document_products", "krai_core.document_products"),
        ("vw_documents", "krai_core.documents"),
        ("vw_embeddings", "ALIAS für vw_chunks", "⚠️ Embeddings sind IN chunks!"),
        ("vw_error_codes", "krai_intelligence.error_codes"),
        ("vw_images", "krai_content.images"),
        ("vw_intelligence_chunks", "krai_intelligence.chunks"),
        ("vw_links", "krai_content.links"),
        ("vw_manufacturers", "krai_core.manufacturers"),
        ("vw_parts", "krai_parts.parts_catalog"),
        ("vw_processing_queue", "krai_system.processing_queue"),
        ("vw_product_series", "krai_core.product_series"),
        ("vw_products", "krai_core.products"),
        ("vw_search_analytics", "krai_intelligence.search_analytics"),
        ("vw_system_metrics", "krai_system.system_metrics"),
        ("vw_video_products", "krai_content.video_products"),
        ("vw_videos", "krai_content.videos"),
        ("vw_webhook_logs", "krai_integrations.webhook_logs"),
    ]
    
    doc.append("| View | Zeigt auf | Hinweis |")
    doc.append("|------|-----------|---------|")
    
    for view_info in existing_views:
        if len(view_info) == 3:
            view, table, note = view_info
            doc.append(f"| `{view}` | `{table}` | {note} |")
        else:
            view, table = view_info
            doc.append(f"| `{view}` | `{table}` | - |")
    
    doc.append("")
    doc.append("---")
    doc.append("")
    doc.append("## Statistik")
    doc.append("")
    doc.append(f"- **Schemas:** {len(schemas)}")
    doc.append(f"- **Tabellen:** {len(tables)}")
    doc.append(f"- **Spalten:** {len(columns)}")
    doc.append("")
    
    # Write to file
    project_root = Path(__file__).parent.parent
    output_file = project_root / "DATABASE_SCHEMA.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(doc))
    
    print(f"\n✅ Dokumentation geschrieben nach: {output_file}")
    print(f"   Schemas: {len(schemas)}")
    print(f"   Tabellen: {len(tables)}")
    print(f"   Spalten: {len(columns)}")
    print("\n" + "="*80)

if __name__ == "__main__":
    generate_doc()
