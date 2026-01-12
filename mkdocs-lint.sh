#!/bin/bash
set -e
markdownlint-cli2 "docs/**/*.md" --config "/app/.markdownlint.json" --fix > lint.log 2>&1 || true