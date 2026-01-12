# MkDocs Exporter Docker

[![Docker Image Build](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml)
[![Container Registry](https://img.shields.io/badge/Container-GHCR-blue?logo=github)](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Alpine Linux](https://img.shields.io/badge/Alpine-Linux-0D597F?logo=alpinelinux&logoColor=white)](https://alpinelinux.org/)

A **streamlined, containerized build environment** for modern documentation workflows. Built on **Python 3.12 Alpine**, this image provides a batteries-included toolchain specifically optimized for **GitHub Actions** and CI/CD pipelines.

> **Note**: This project uses a "Configuration-as-Data" approach — automatically generating `mkdocs.yml` at runtime by merging internal templates with your project metadata.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Usage](#usage)
  - [GitHub Actions (Recommended)](#github-actions-recommended)
  - [Local Development](#local-development)
  - [Makefile Integration](#makefile-integration)
- [Configuration](#configuration)
  - [Directory Structure](#directory-structure)
  - [info.json Format](#infojson-format)
- [Available Commands](#available-commands)
- [Technical Details](#technical-details)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Feature | Description |
|---------|-------------|
| 🚀 **Lightweight** | Built on Alpine Linux (~50MB base), ensuring rapid image pulls and minimal CI resource usage |
| 🧩 **Dynamic Configuration** | Auto-generates `mkdocs.yml` from `info.json`, templates, and local overrides |
| 🔋 **Batteries Included** | Pre-configured with essential MkDocs plugins and extensions |
| 🛠 **CI/CD Optimized** | Includes `bash`, `git`, `nodejs`, and other tools for seamless GitHub Actions integration |
| 📝 **Markdown Linting** | Built-in `markdownlint-cli2` for automatic style enforcement |
| ⚡ **Multiple Serve Modes** | Standard `mkdocs serve` and high-performance `zensical serve` |

### Pre-installed Plugins & Extensions

**MkDocs Plugins:**
- `mkdocs-glightbox` — Image lightbox/zooming
- `mkdocs-minify-plugin` — HTML minification for production

**Markdown Extensions:**
- `pymdown-extensions` — Advanced syntax (arithmatex, highlight, snippets, etc.)
- Full `mkdocs-material` feature support (navigation, search, code copy, etc.)

---

## Quick Start

```bash
# Pull the image
docker pull ghcr.io/raineblog/mkdocs-docker:latest

# Build documentation
docker run --rm -v $(pwd):/app/workspace -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest mkdocs-build

# Serve with live-reload
docker run --rm -it -p 8000:8000 -v $(pwd):/app/workspace -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest mkdocs-serve
```

---

## Architecture

This builder uses a **"Configuration-as-Data"** approach. Instead of manually maintaining a complex `mkdocs.yml`, the environment generates it at runtime by merging three sources:

---

## Usage

### GitHub Actions (Recommended)

Use this image as a job container in your workflow:

```yaml
name: Build and Deploy Documentation

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/raineblog/mkdocs-docker:latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Build Documentation
        run: mkdocs-build

      - name: Deploy to GitHub Pages
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./site
```

### Local Development

**Build documentation:**

```bash
docker run --rm \
  -v $(pwd):/app/workspace \
  -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest \
  mkdocs-build
```

**Serve with live-reload (Linux/macOS):**

```bash
docker run --rm -it \
  -v $(pwd):/app/workspace \
  -w /app/workspace \
  -p 8000:8000 \
  ghcr.io/raineblog/mkdocs-docker:latest \
  mkdocs-serve
```

**Serve with live-reload (Windows PowerShell):**

```powershell
docker run --rm -it --init `
  -v ${pwd}:/app/workspace `
  -w /app/workspace `
  -p 8000:8000 `
  ghcr.io/raineblog/mkdocs-docker:latest `
  mkdocs-serve
```

### Makefile Integration

```makefile
.PHONY: serve build lint pull

IMAGE := ghcr.io/raineblog/mkdocs-docker:latest

serve:
	docker run --rm -it --init -p 8000:8000 \
		-v $(CURDIR):/app/workspace -w /app/workspace \
		$(IMAGE) mkdocs-serve

build:
	docker run --rm \
		-v $(CURDIR):/app/workspace -w /app/workspace \
		$(IMAGE) mkdocs-build

lint:
	docker run --rm \
		-v $(CURDIR):/app/workspace -w /app/workspace \
		$(IMAGE) mkdocs-lint

pull:
	docker pull $(IMAGE)
```

---

## Configuration

### Directory Structure

Your project must follow this structure:

```text
.
├── info.json                 # Required: Project metadata & navigation
├── docs/                     # Required: Markdown content
│   ├── index.md              # Required: Homepage
│   ├── intro/                # Required: Introduction section
│   │   ├── format.md
│   │   ├── usage.md
│   │   └── discussion.md
│   ├── madoka.md             # Required: Part of intro
│   └── assets/               # Optional
│       └── extra.yml         # Optional: MkDocs config overrides
├── includes/                 # Optional: Snippets for inclusion
│   └── abbreviations.md      # Optional: Abbreviation definitions
└── .markdownlint.json        # Optional: Custom linting rules
```

> [!IMPORTANT]
> This builder is **opinionated** and automatically prepends several "Introduction" pages to your navigation. Ensure these required files exist in your `docs/` folder to avoid build errors.

### info.json Format

The `info.json` file is the heart of your documentation metadata:

```json
{
  "project": {
    "site_name": "My Documentation",
    "site_description": "A wonderful project description",
    "repo_url": "https://github.com/user/repo"
  },
  "nav": [
    {
      "title": "Getting Started",
      "children": [
        "guide/install.md",
        "guide/config.md"
      ]
    },
    {
      "title": "Reference",
      "children": [
        "reference/api.md",
        "reference/cli.md"
      ]
    }
  ],
  "extra": {
    "version": "1.0.0",
    "social": [
      { "icon": "fontawesome/brands/github", "link": "https://github.com/user" }
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `project` | Object | Core MkDocs settings (site_name, site_description, repo_url, etc.) |
| `nav` | Array | Navigation structure with title and children |
| `extra` | Object | Additional MkDocs extra configuration |

---

## Available Commands

| Command | Description |
|---------|-------------|
| `mkdocs-build` | Full build pipeline: lint → generate config → build → sync artifacts |
| `mkdocs-serve` | Start development server with live-reload on port 8000 |
| `mkdocs-lint` | Run Markdown linting with auto-fix |
| `zensical-serve` | Alternative high-performance server (fewer features, faster startup) |

### Build Pipeline Details

The `mkdocs-build` command executes these steps:

1. **Lint** — Run `markdownlint-cli2` with auto-fix
2. **Generate** — Create `mkdocs.yml` from templates and `info.json`
3. **Build** — Execute `mkdocs build --strict --clean`
4. **Sync** — Merge any static assets from `public/` into `site/`

---

## Technical Details

### Base Image

- **Python 3.12 Alpine** — Minimal footprint, fast startup
- Multi-stage build to include `markdownlint-cli2` from Node.js

### Installed System Packages

| Package | Purpose |
|---------|---------|
| `bash` | Shell scripts execution |
| `git` | Version control, mkdocs-git plugins |
| `nodejs` | Markdown linting runtime |
| `ca-certificates` | HTTPS support |

### Python Dependencies

```text
pyyaml              # YAML parsing
mkdocs              # Static site generator
mkdocs-glightbox    # Image lightbox
mkdocs-minify-plugin # HTML minification
pymdown-extensions  # Markdown extensions
zensical            # High-performance server
```

---

## Contributing

This project is a **personal toolchain** maintained by [@raineblog](https://github.com/raineblog).

| Type | Status |
|------|--------|
| 🐛 Bug Reports | ✅ Welcome |
| 📝 Corrections | ✅ Welcome (typos, documentation fixes) |
| 🔒 Security Patches | ✅ Welcome |
| ✨ Feature Requests | ❌ Not accepting |
| 🔀 Pull Requests (new features) | ❌ Not accepting |

> **Why no feature requests?**
> This tool is designed to be highly specialized for a specific workflow. If you need more flexibility or additional features, I recommend using the official [squidfunk/mkdocs-material](https://github.com/squidfunk/mkdocs-material) Docker image.

### Reporting Issues

If you encounter a bug, please [open an issue](https://github.com/raineblog/mkdocs-docker/issues/new) with:

- Docker version and host OS
- Command that triggered the error
- Full error output
- Minimal reproduction steps (if possible)

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for more information.

```text
MIT License

Copyright (c) 2026 RainPPR

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

<div align="center">

**[Container Registry](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)** · **[Report Bug](https://github.com/raineblog/mkdocs-docker/issues)** · **[View Source](https://github.com/raineblog/mkdocs-docker)**

</div>

---

<sub>
📝 <strong>Documentation Notice</strong>: This README was generated by <strong>Antigravity (Claude Opus 4.5)</strong>, an AI coding assistant developed by Google DeepMind, and has been reviewed and approved by a human maintainer.
</sub>
