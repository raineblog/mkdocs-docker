#!/bin/bash
set -e
python /app/scripts/generate.serve.py "$@"
mkdocs serve --dirty --livereload --dev-addr 0.0.0.0:8000
