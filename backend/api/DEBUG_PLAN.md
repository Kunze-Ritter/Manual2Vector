# DEBUG PLAN: Warum ist solution_text nur 18 Zeichen?

## Problem
- C9402 solution_text in DB: "1. Correct the har" (18 chars)
- Sollte vollständige Lösung sein

## Hypothesen

### 1. Pattern matched nicht richtig
- `_extract_solution()` findet die Lösung nicht
- Fällt zurück auf "No solution found"

### 2. Text wird abgeschnitten BEVOR extraction
- PDF-Text-Extraktion schneidet ab
- `code_end_pos + 5000` reicht nicht

### 3. Regex Pattern schneidet ab
- Pattern matched nur ersten Teil
- Zeile 658: `for line in lines[:20]` - nimmt nur 20 Zeilen
- Zeile 663: `if len(line.strip()) > 20` - stoppt bei kurzen Zeilen?

### 4. Database INSERT schneidet ab
- VARCHAR limit in DB?
- Supabase Function schneidet ab?

## Nächste Schritte

1. **Check DB Schema**
   ```sql
   SELECT column_name, data_type, character_maximum_length
   FROM information_schema.columns
   WHERE table_name = 'error_codes' AND column_name = 'solution_text';
   ```

2. **Check was wirklich extrahiert wird**
   - Log hinzufügen in `_extract_solution()`
   - Zeigen was matched wird

3. **Check PDF Text**
   - Ist die vollständige Lösung im PDF-Text?
   - Oder ist das PDF selbst unvollständig?

## Quick Fix Option
Wenn Pattern das Problem ist:
- Zeile 658: `lines[:20]` → `lines[:50]`
- Zeile 684: `[:1000]` → `[:3000]`
- Zeile 691: `lines[:15]` → `lines[:30]`
