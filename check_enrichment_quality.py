"""Check quality of error code enrichment"""
import os
from dotenv import load_dotenv
from pathlib import Path
from supabase import create_client

load_dotenv(Path('.env.database'))
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))

print("Prüfe Enrichment-Qualität...\n")

# Get sample error codes
errors = client.table('vw_error_codes').select(
    'error_code, error_description, chunk_id, confidence_score, document_id'
).not_.is_('chunk_id', 'null').limit(10).execute()

print(f"Fehlercodes mit chunk_id: {len(errors.data)}\n")

for i, error in enumerate(errors.data[:5], 1):
    code = error.get('error_code')
    desc = error.get('error_description', 'N/A')
    conf = error.get('confidence_score', 0)
    chunk_id = error.get('chunk_id')
    
    print(f"{i}. {code} (Confidence: {conf:.2f})")
    print(f"   📝 {desc[:80]}")
    
    # Check chunk content
    if chunk_id:
        chunk = client.table('vw_intelligence_chunks').select(
            'text_chunk'
        ).eq('id', chunk_id).limit(1).execute()
        
        if chunk.data:
            text = chunk.data[0].get('text_chunk', '')
            # Check if error code is in chunk
            if code in text:
                print(f"   ✅ Fehlercode im Chunk gefunden")
            else:
                print(f"   ❌ Fehlercode NICHT im Chunk!")
            
            # Check for solution keywords
            has_solution = any(kw in text.lower() for kw in ['recommended action', 'procedure', 'solution', 'replace', 'check'])
            if has_solution:
                print(f"   ✅ Lösungs-Keywords gefunden")
            else:
                print(f"   ⚠️  Keine Lösungs-Keywords")
        
        # Check images
        images = client.table('vw_images').select('id, storage_url').eq(
            'chunk_id', chunk_id
        ).execute()
        
        if images.data:
            print(f"   🖼️  {len(images.data)} Bilder verknüpft")
        else:
            print(f"   ⚠️  Keine Bilder")
    
    print()

print("\n📊 Zusammenfassung:")
print(f"- Fehlercodes mit Chunks: {len(errors.data)}")
print(f"- Durchschnittliche Confidence: {sum(e.get('confidence_score', 0) for e in errors.data) / len(errors.data):.2f}")
