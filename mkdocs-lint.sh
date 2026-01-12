#!/bin/bash
set -e
markdownlint-cli2 "docs/**/*.md" --config ".markdownlint.json" --fix || true
