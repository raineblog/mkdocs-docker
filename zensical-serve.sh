#!/bin/bash
set -e
python /app/scripts/generate.serve.py "$@"
zensical serve --dev-addr 0.0.0.0:8000
