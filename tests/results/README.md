# Test Results Directory

This directory stores test execution results and artifacts.

## Structure

- `archive/` - Historical test results (JSON, logs, reports)
- Current test runs output to this directory

## .gitignore

This entire directory is excluded from version control to prevent
committing test artifacts and large result files.

## Cleanup

Test results can be safely deleted when no longer needed.
Archive subdirectory preserves historical results for reference.
