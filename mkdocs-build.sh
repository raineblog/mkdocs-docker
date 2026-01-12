#!/bin/bash
set -e

echo "========================================"
echo ">>> [1/4] Starting Linting Process..."
echo ">>> Linter: markdownlint-cli2"
markdownlint-cli2 "docs/**/*.md" --config ".markdownlint.json" --fix > lint.log 2>&1 || true
echo ">>> Linting finished. Results saved to lint.log (if any errors occurred, they were attempted to be fixed)."
echo "========================================"

echo ">>> [2/4] Running Python generation script..."
echo ">>> Container Workdir: $(pwd)"
# "$@" 表示将传递给 shell 脚本的所有参数透传给 python 脚本
python /app/scripts/generate.py "$@"
echo ">>> Generation script finished."
echo "========================================"

echo ">>> [3/4] Running MkDocs build..."
mkdocs build --strict --clean
echo ">>> MkDocs build finished."
echo "========================================"

echo ">>> [4/4] Syncing build artifacts..."
python -c "import shutil; shutil.copytree('public', 'site', dirs_exist_ok=True)"
echo ">>> Sync finished."
echo "========================================"

echo ">>> [SUCCESS] All steps completed successfully."
