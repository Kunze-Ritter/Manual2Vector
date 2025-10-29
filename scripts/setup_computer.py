"""
Setup Script für Multi-Computer Environment

Erstellt automatisch die richtige .env basierend auf dem aktuellen Computer.
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Setup .env für aktuellen Computer"""
    
    # Aktuelles Verzeichnis ermitteln
    project_root = Path(__file__).parent
    
    print("🔧 KRAI Environment Setup")
    print("=" * 60)
    print(f"Project Root: {project_root}")
    print()
    
    # Prüfe ob .env existiert
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"
    
    if env_file.exists():
        print("✅ .env already exists")
        response = input("   Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("❌ Aborted")
            return
    
    # Kopiere .env.example zu .env
    if not env_example.exists():
        print("❌ .env.example not found!")
        return
    
    shutil.copy(env_example, env_file)
    print("✅ Created .env from .env.example")
    print()
    
    # Computer-spezifische Anpassungen
    print("📝 Please configure the following in .env:")
    print("   1. SUPABASE_URL")
    print("   2. SUPABASE_SERVICE_ROLE_KEY")
    print("   3. R2_ACCESS_KEY_ID")
    print("   4. R2_SECRET_ACCESS_KEY")
    print("   5. YOUTUBE_API_KEY")
    print()
    print(f"📂 Edit: {env_file}")
    print()
    print("💡 Tip: Never commit .env to git!")
    print("   It's already in .gitignore")

if __name__ == "__main__":
    setup_environment()
