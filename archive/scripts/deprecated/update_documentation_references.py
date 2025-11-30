#!/usr/bin/env python3
"""
Update Documentation References Script

This script systematically updates Supabase and R2 references across all documentation files
to use the new PostgreSQL and MinIO variable names.

Usage:
    python scripts/update_documentation_references.py [options]

Options:
    --dry-run       Preview changes without modifying files
    --verbose       Show detailed output
    --path PATH     Specify directory to process (default: entire repo)
    --backup        Create backups before modifying files
"""

import argparse
import logging
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Variable replacement mappings
DATABASE_REPLACEMENTS = {
    'SUPABASE_URL': 'DATABASE_CONNECTION_URL',
    'SUPABASE_ANON_KEY': '# Not needed (PostgreSQL uses password auth)',
    'SUPABASE_SERVICE_ROLE_KEY': '# Not needed (PostgreSQL uses password auth)',
    'SUPABASE_STORAGE_URL': 'OBJECT_STORAGE_ENDPOINT',
    'SUPABASE_DB_PASSWORD': 'DATABASE_PASSWORD',
    'DATABASE_URL': 'DATABASE_CONNECTION_URL',
}

STORAGE_REPLACEMENTS = {
    'R2_ACCESS_KEY_ID': 'OBJECT_STORAGE_ACCESS_KEY',
    'R2_SECRET_ACCESS_KEY': 'OBJECT_STORAGE_SECRET_KEY',
    'R2_ENDPOINT_URL': 'OBJECT_STORAGE_ENDPOINT',
    'R2_BUCKET_NAME_DOCUMENTS': '# Managed by MinIO bucket configuration',
    'R2_REGION': 'OBJECT_STORAGE_REGION',
    'R2_PUBLIC_URL_DOCUMENTS': 'OBJECT_STORAGE_PUBLIC_URL',
    'R2_PUBLIC_URL_ERROR': 'OBJECT_STORAGE_PUBLIC_URL',
    'R2_PUBLIC_URL_PARTS': 'OBJECT_STORAGE_PUBLIC_URL',
    'UPLOAD_IMAGES_TO_R2': '# Not needed (MinIO is default)',
    'UPLOAD_DOCUMENTS_TO_R2': '# Not needed (MinIO is default)',
    'MINIO_ENDPOINT': 'OBJECT_STORAGE_ENDPOINT',
    'MINIO_ACCESS_KEY': 'OBJECT_STORAGE_ACCESS_KEY',
    'MINIO_SECRET_KEY': 'OBJECT_STORAGE_SECRET_KEY',
}

AI_REPLACEMENTS = {
    'OLLAMA_BASE_URL': 'OLLAMA_URL',
    'AI_SERVICE_URL': 'OLLAMA_URL',
}

# Combine all replacements
ALL_REPLACEMENTS = {
    **DATABASE_REPLACEMENTS,
    **STORAGE_REPLACEMENTS,
    **AI_REPLACEMENTS,
}

# Directories to exclude from search
EXCLUDE_DIRS = {
    '.git',
    'node_modules',
    'venv',
    '.venv',
    '__pycache__',
    'dist',
    'build',
    '.cache',
    'coverage',
    'htmlcov',
    '.pytest_cache',
    '.mypy_cache',
    'frontend/dist',
    'frontend/build',
    'frontend/node_modules',
}

# Files to exclude from processing
EXCLUDE_FILES = {
    '.env',
    '.env.local',
    '.env.production',
    '.env.development',
    '.env.test',
}

# Files where legacy variable names should be preserved (intentionally documented)
PRESERVE_LEGACY_FILES = {
    'docs/setup/DEPRECATED_VARIABLES.md',
    'docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md',
    'DEPRECATED_VARIABLES.md',
    'SUPABASE_TO_POSTGRESQL_MIGRATION.md',
}


class DocumentationUpdater:
    """Updates documentation references from Supabase/R2 to PostgreSQL/MinIO."""

    def __init__(self, dry_run: bool = False, verbose: bool = False, backup: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.backup = backup
        self.files_scanned = 0
        self.files_modified = 0
        self.replacements_made = 0
        self.errors: List[Tuple[str, str]] = []

    def find_markdown_files(self, search_path: Path) -> List[Path]:
        """Find all markdown files in the search path."""
        markdown_files = []
        
        for path in search_path.rglob('*.md'):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
                continue
            
            # Skip excluded files
            if path.name in EXCLUDE_FILES:
                continue
            
            markdown_files.append(path)
        
        return sorted(markdown_files)

    def is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read(1024)  # Read first 1KB
            return True
        except (UnicodeDecodeError, PermissionError):
            return False

    def create_backup(self, file_path: Path) -> None:
        """Create a backup of the file."""
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        shutil.copy2(file_path, backup_path)
        if self.verbose:
            logger.info(f"  Created backup: {backup_path}")

    def replace_in_content(self, content: str, file_path: Path) -> Tuple[str, int]:
        """Replace deprecated variables in content, preserving markdown formatting."""
        # Check if this file should preserve legacy variable names
        file_path_str = str(file_path).replace('\\', '/')
        if any(preserve_file in file_path_str for preserve_file in PRESERVE_LEGACY_FILES):
            if self.verbose:
                logger.info(f"  Skipping {file_path} (legacy documentation)")
            return content, 0
        
        modified_content = content
        replacements_count = 0

        for old_var, new_var in ALL_REPLACEMENTS.items():
            # Skip deprecation notes (variables that map to comments)
            is_deprecation_note = new_var.startswith('#')
            
            # Pattern 1: Inline code with backticks `VARIABLE_NAME`
            inline_code_pattern = rf'`{old_var}`'
            inline_matches = re.findall(inline_code_pattern, modified_content)
            if inline_matches and not is_deprecation_note:
                # Preserve backticks in replacement
                modified_content = re.sub(inline_code_pattern, f'`{new_var}`', modified_content)
                replacements_count += len(inline_matches)
                if self.verbose:
                    logger.info(f"  Replaced {len(inline_matches)}x inline code: `{old_var}` -> `{new_var}`")
            
            # Pattern 2: Shell variable assignments (e.g., VARIABLE_NAME=value)
            # Only match at start of line or after whitespace
            shell_assignment_pattern = rf'(^|\s)({old_var})='
            shell_matches = re.findall(shell_assignment_pattern, modified_content, re.MULTILINE)
            if shell_matches and not is_deprecation_note:
                modified_content = re.sub(
                    shell_assignment_pattern,
                    rf'\1{new_var}=',
                    modified_content,
                    flags=re.MULTILINE
                )
                replacements_count += len(shell_matches)
                if self.verbose:
                    logger.info(f"  Replaced {len(shell_matches)}x shell assignment: {old_var}= -> {new_var}=")
            
            # Pattern 3: Shell variable references ${VARIABLE_NAME}
            shell_ref_braces_pattern = rf'\${{{old_var}}}'
            shell_ref_matches = re.findall(shell_ref_braces_pattern, modified_content)
            if shell_ref_matches and not is_deprecation_note:
                modified_content = re.sub(shell_ref_braces_pattern, f'${{{new_var}}}', modified_content)
                replacements_count += len(shell_ref_matches)
                if self.verbose:
                    logger.info(f"  Replaced {len(shell_ref_matches)}x shell ref: ${{{old_var}}} -> ${{{new_var}}}")
            
            # Pattern 4: Shell variable references $VARIABLE_NAME (without braces)
            shell_ref_pattern = rf'\$({old_var})\b'
            shell_ref_simple_matches = re.findall(shell_ref_pattern, modified_content)
            if shell_ref_simple_matches and not is_deprecation_note:
                modified_content = re.sub(shell_ref_pattern, f'${new_var}', modified_content)
                replacements_count += len(shell_ref_simple_matches)
                if self.verbose:
                    logger.info(f"  Replaced {len(shell_ref_simple_matches)}x shell ref: ${old_var} -> ${new_var}")
            
            # Pattern 5: Plain text references (be conservative - only in prose)
            # Skip if inside code blocks or if it's a deprecation note
            if not is_deprecation_note:
                # Only match word boundaries to avoid partial matches
                plain_text_pattern = rf'\b{old_var}\b'
                # Exclude matches that are:
                # - Inside backticks (already handled)
                # - Part of shell assignments (already handled)
                # - Inside code blocks (between ``` markers)
                
                # Split content by code blocks
                parts = re.split(r'(```[\s\S]*?```)', modified_content)
                modified_parts = []
                
                for i, part in enumerate(parts):
                    # Only process non-code-block parts (even indices)
                    if i % 2 == 0:
                        # Skip if already in backticks or shell context
                        if f'`{old_var}' not in part and f'{old_var}=' not in part and f'${old_var}' not in part:
                            plain_matches = re.findall(plain_text_pattern, part)
                            if plain_matches:
                                part = re.sub(plain_text_pattern, new_var, part)
                                replacements_count += len(plain_matches)
                                if self.verbose:
                                    logger.info(f"  Replaced {len(plain_matches)}x plain text: {old_var} -> {new_var}")
                    modified_parts.append(part)
                
                modified_content = ''.join(modified_parts)

        return modified_content, replacements_count

    def process_file(self, file_path: Path) -> bool:
        """Process a single file."""
        self.files_scanned += 1

        # Check if file is text
        if not self.is_text_file(file_path):
            if self.verbose:
                logger.warning(f"Skipping non-text file: {file_path}")
            return False

        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # Replace deprecated variables
            modified_content, replacements_count = self.replace_in_content(
                original_content, file_path
            )

            # Check if file was modified
            if modified_content != original_content:
                if self.dry_run:
                    logger.info(f"Would modify: {file_path} ({replacements_count} replacements)")
                else:
                    # Create backup if requested
                    if self.backup:
                        self.create_backup(file_path)

                    # Write modified content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_content)

                    logger.info(f"Modified: {file_path} ({replacements_count} replacements)")

                self.files_modified += 1
                self.replacements_made += replacements_count
                return True

        except Exception as e:
            error_msg = f"Error processing {file_path}: {str(e)}"
            logger.error(error_msg)
            self.errors.append((str(file_path), str(e)))
            return False

        return False

    def process_directory(self, search_path: Path) -> None:
        """Process all markdown files in directory."""
        logger.info(f"Searching for markdown files in: {search_path}")
        
        markdown_files = self.find_markdown_files(search_path)
        logger.info(f"Found {len(markdown_files)} markdown files")

        if self.dry_run:
            logger.info("DRY RUN MODE - No files will be modified")

        for file_path in markdown_files:
            if self.verbose:
                logger.info(f"Processing: {file_path}")
            self.process_file(file_path)

    def print_summary(self) -> None:
        """Print summary of changes."""
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Files scanned:       {self.files_scanned}")
        print(f"Files modified:      {self.files_modified}")
        print(f"Replacements made:   {self.replacements_made}")
        print(f"Errors encountered:  {len(self.errors)}")

        if self.dry_run:
            print("\nDRY RUN MODE - No files were actually modified")

        if self.errors:
            print("\nERRORS:")
            for file_path, error in self.errors:
                print(f"  {file_path}: {error}")

        print("\nVariable Mappings Used:")
        print("-" * 70)
        print("Database Variables:")
        for old, new in DATABASE_REPLACEMENTS.items():
            print(f"  {old:30} -> {new}")
        
        print("\nStorage Variables:")
        for old, new in STORAGE_REPLACEMENTS.items():
            print(f"  {old:30} -> {new}")
        
        print("\nAI Service Variables:")
        for old, new in AI_REPLACEMENTS.items():
            print(f"  {old:30} -> {new}")

        print("\nFor more information, see:")
        print("  - docs/SUPABASE_TO_POSTGRESQL_MIGRATION.md")
        print("  - docs/setup/DEPRECATED_VARIABLES.md")
        print("=" * 70)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update documentation references from Supabase/R2 to PostgreSQL/MinIO',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Preview changes without modifying files
  python scripts/update_documentation_references.py --dry-run

  # Update all documentation with backups
  python scripts/update_documentation_references.py --backup

  # Update specific directory with verbose output
  python scripts/update_documentation_references.py --path docs/setup/ --verbose

  # Generate report
  python scripts/update_documentation_references.py --dry-run --verbose > report.txt
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )

    parser.add_argument(
        '--path',
        type=str,
        default='.',
        help='Directory to process (default: current directory)'
    )

    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create backups before modifying files'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Resolve search path
    search_path = Path(args.path).resolve()
    if not search_path.exists():
        logger.error(f"Path does not exist: {search_path}")
        sys.exit(1)

    # Create updater and process files
    updater = DocumentationUpdater(
        dry_run=args.dry_run,
        verbose=args.verbose,
        backup=args.backup
    )

    try:
        updater.process_directory(search_path)
        updater.print_summary()
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        updater.print_summary()
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

    # Exit with appropriate code
    if updater.errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
