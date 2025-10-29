@echo off
echo ========================================
echo Applying Migration 81: vw_parts View
echo ========================================
echo.

cd backend\api
python -c "from pathlib import Path; from dotenv import load_dotenv; import os; from supabase import create_client; project_root = Path.cwd().parent.parent; load_dotenv(project_root / '.env.database'); supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY')); sql = (project_root / 'database' / 'migrations' / '81_create_vw_parts_view.sql').read_text(encoding='utf-8'); result = supabase.rpc('exec_sql', {'sql_query': sql}).execute(); print('✅ Migration 81 applied successfully!' if result else '❌ Migration failed')"

echo.
echo ========================================
echo Done!
echo ========================================
pause
