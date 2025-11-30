@echo off
echo ========================================
echo Applying Migration 81: vw_parts View
echo ========================================
echo.

cd backend\api
python -c "from pathlib import Path; import os; import sys; project_root = Path.cwd().parent.parent; sys.path.insert(0, str(project_root)); from scripts._env import load_env; load_env(extra_files=['.env.database']); from supabase import create_client; sql = (project_root / 'database' / 'migrations' / '81_create_vw_parts_view.sql').read_text(encoding='utf-8'); supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY')); result = supabase.rpc('exec_sql', {'sql_query': sql}).execute(); print('✅ Migration 81 applied successfully!' if result else '❌ Migration failed')"

echo.
echo ========================================
echo Done!
echo ========================================
pause
