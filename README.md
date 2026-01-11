# MkDocs Exporter Docker

[![Docker Image](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml)
[![Registry](https://img.shields.io/badge/Container-GHCR-blue?logo=github)](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)

**MkDocs Exporter Docker** is a streamlined, containerized build environment designed for modern documentation workflows. Based on **Python 3.12 Alpine**, it provides a "batteries-included" toolchain specifically optimized for **GitHub Actions** and CI/CD pipelines.

---

## ✨ Key Features

-   **🚀 Fast & Lightweight**: Built on Alpine Linux to ensure rapid image pulls and minimal resource footprint in CI environments.
-   **🧩 Dynamic Configuration**: Automatically assembles your `mkdocs.yml` from separate sources (`info.json`, templates, and local overrides), allowing for easier metadata management.
-   **🔋 Batteries Included**: Pre-configured with essential plugins:
    -   `mkdocs-material` features (pre-configured)
    -   `mkdocs-glightbox` for image zooming
    -   `mkdocs-minify-plugin` for production optimization
    -   `pymdown-extensions` for advanced Markdown syntax
-   **🛠 GitHub Actions Optimized**: Includes `bash`, `git`, `tar`, and `gzip` to support common GHA steps seamlessly.
-   **⚡ Specialized Serving**: Support for standard `mkdocs serve` and the specialized `zensical serve`.

---

## 🏗 How It Works

This builder uses a "Configuration-as-Data" approach. Instead of manually maintaining a complex `mkdocs.yml`, the environment generates it at runtime by merging three sources:

1.  **Internal Template**: Base settings for theme, plugins, and extensions.
2.  **`info.json`**: Your project's core metadata (name, description, navigation).
3.  **`docs/assets/extra.yml`**: Any project-specific overrides or additional MkDocs configuration.

### Directory Structure Requirement
To use this image, your project should follow this structure:
```text
.
├── info.json               # Required: Project metadata & Nav
├── docs/                   # Required: Markdown content
│   ├── index.md            # Required (used in intro)
│   ├── intro/              # Required (used in intro)
│   │   ├── format.md
│   │   ├── usage.md
│   │   └── discussion.md
│   ├── madoka.md           # Required (used in intro)
│   └── assets/             # Optional
│       └── extra.yml       # Optional: MkDocs overrides
└── ...
```

> [!NOTE]
> This builder is opinionated and automatically prepends several "Introduction" pages to your navigation. Ensure these files exist in your `docs/` folder to avoid build errors.

---

## 🚀 Usage

### 1. GitHub Actions (Recommended)
Add this image as a job container in your `.github/workflows/deploy.yml`:

```yaml
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

### 2. Local Development
You can mirror the production build process locally:

```bash
docker run --rm \
  -v $(pwd):/app/workspace \
  -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest \
  mkdocs-build
```

To serve documentation with live-reload:
```bash
docker run --rm -it \
  -v $(pwd):/app/workspace \
  -w /app/workspace \
  -p 8000:8000 \
  ghcr.io/raineblog/mkdocs-docker:latest \
  mkdocs-serve
```

To serve documentation with live-reload in Windows pwsh:
```pwsh
docker run --rm -it --init \
  -v ${pwd}:/app/workspace \
  -w /app/workspace \
  -p 8000:8000 \
  ghcr.io/raineblog/mkdocs-docker:latest \
  mkdocs-serve
```

You can replace `mkdocs-serve` with `zensical-serve` for a better performance but with fewer features support. **NOT RECOMMENDED** for publish.

---

## ⚙️ Configuration Reference

### `info.json` Format
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
    }
  ],
  "extra": {
    "version": "1.0.0"
  }
}
```

---

## 🛠 Maintenance & Community

This project is a personal toolchain maintained by **raineblog**.

-   **Status**: Active / Low-Maintenance.
-   **Contributions**: I am happy to accept **bug reports** and **corrections** (typos, logic fixes, security patches).
-   **Feature Requests**: I am currently **not accepting new features**. The tool is designed to be highly specialized for my specific workflow; if you need more flexibility, I recommend using the official [Squidfunk/mkdocs-material](https://github.com/squidfunk/mkdocs-material) image.

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.
