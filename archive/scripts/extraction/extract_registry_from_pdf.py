"""
Extract Registry data from opened Foliant PDF
This requires the PDF to be opened in Adobe Acrobat Reader
"""
import subprocess
import time
import os

def open_pdf_and_wait(pdf_path):
    """Open PDF in Adobe Reader and wait for user to interact"""
    
    print("=" * 80)
    print("FOLIANT REGISTRY EXTRACTOR")
    print("=" * 80)
    
    print(f"\nOpening PDF: {pdf_path}")
    
    # Open with default PDF viewer
    os.startfile(pdf_path)
    
    print("\n" + "=" * 80)
    print("INSTRUCTIONS")
    print("=" * 80)
    print("""
1. Die PDF sollte sich jetzt in Adobe Reader öffnen
2. Klicke auf verschiedene Optionen um die Kompatibilität zu testen
3. Öffne die JavaScript-Konsole:
   - Drücke Ctrl+J (oder Strg+J)
   - Oder: Bearbeiten → Voreinstellungen → JavaScript → Debugger aktivieren
   
4. In der Konsole, gib ein:

   Registry.System.Logic.Enabled
   Registry.System.Logic.Groups
   Registry.System.Atoms
   
5. Kopiere die Ausgabe und speichere sie als:
   - registry_enabled.txt
   - registry_groups.txt
   - registry_atoms.txt

ALTERNATIVE: Export als XML
============================
In der Konsole:

console.println(Registry.System.Logic.toXMLString())
console.println(Registry.System.Atoms.toXMLString())

Dann: Rechtsklick auf Ausgabe → Kopieren → In Datei speichern

""")
    
    input("\nDrücke ENTER wenn du fertig bist...")
    
    print("\n✅ Gut! Jetzt können wir die Daten analysieren.")
    print("\nWenn du die Registry-Daten gespeichert hast, können wir sie parsen!")

def create_manual_extraction_guide():
    """Create a guide for manual extraction"""
    
    guide = """
# FOLIANT REGISTRY EXTRACTION GUIDE

## Methode 1: JavaScript-Konsole (Empfohlen)

1. Öffne die PDF in Adobe Acrobat Reader DC
2. Drücke Ctrl+J um die JavaScript-Konsole zu öffnen
3. Gib folgende Befehle ein:

```javascript
// Export Logic Registry
console.println("=== LOGIC REGISTRY ===");
console.println(Registry.System.Logic.toXMLString());

// Export Atoms Registry  
console.println("=== ATOMS REGISTRY ===");
console.println(Registry.System.Atoms.toXMLString());

// Export Enabled List
console.println("=== ENABLED LIST ===");
console.println(Registry.System.Logic.Enabled.toString());

// Export Groups
console.println("=== GROUPS ===");
console.println(Registry.System.Logic.Groups.toXMLString());
```

4. Kopiere die gesamte Ausgabe
5. Speichere als: `foliant_registry_export.txt`

## Methode 2: Einzelne Abfragen

```javascript
// Welche Optionen sind aktiviert?
Registry.System.Logic.Enabled.toString()

// Welche Gruppen gibt es?
Registry.System.Logic.Groups.toXMLString()

// Alle Items
Registry.System.Atoms.Item.toXMLString()

// Auswahl-Status
Registry.System.Logic.Selection.toString()
```

## Methode 3: Alle Sprites auflisten

```javascript
// Liste aller Sprite-Namen
var sprites = [];
for (var i = 0; i < this.numFields; i++) {
    var field = this.getNthFieldName(i);
    if (field.indexOf("Sprite_") === 0) {
        sprites.push(field.replace("Sprite_", ""));
    }
}
console.println(sprites.join(";"));
```

## Was wir brauchen:

- **Enabled**: Welche Optionen sind verfügbar
- **Groups**: Wie sind Optionen gruppiert (links/rechts/oben/unten)
- **Atoms**: Alle verfügbaren Items mit ihren Properties
- **FunctionGroups.Choice**: Auswahl-Logik und Abhängigkeiten

"""
    
    with open('FOLIANT_EXTRACTION_GUIDE.md', 'w', encoding='utf-8') as f:
        f.write(guide)
    
    print("✅ Guide erstellt: FOLIANT_EXTRACTION_GUIDE.md")

if __name__ == "__main__":
    pdf_path = r"C:\Users\haast\Docker\KRAI-minimal\input_foliant\processed\Foliant bizhub C257i v1.10 R1.pdf"
    
    # Create guide
    create_manual_extraction_guide()
    
    print("\n" + "=" * 80)
    print("Möchtest du die PDF jetzt öffnen? (j/n)")
    response = input("> ")
    
    if response.lower() in ['j', 'y', 'yes', 'ja']:
        open_pdf_and_wait(pdf_path)
    else:
        print("\nOK! Lies die Anleitung in FOLIANT_EXTRACTION_GUIDE.md")
        print("Wenn du die Registry-Daten hast, können wir sie analysieren!")
