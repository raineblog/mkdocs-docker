# MkDocs Exporter Docker

[![Docker Image](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml)
[![Registry](https://img.shields.io/badge/Container-GHCR-blue)](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)

A streamlined, Dockerized MkDocs build environment based on **Python 3.12 Alpine**. This project is designed to provide a consistent, containerized toolchain for building documentation with a pre-configured set of plugins and a dynamic configuration generator.

## 🚀 Overview

This image simplifies the MkDocs build process by:

1. **Dynamic Configuration**: Automatically merging metadata (`info.json`) and specific YAML fragments into a final `mkdocs.yml`.
2. **Batteries Included**: Pre-installed with essential plugins like `glightbox`, `minify`, and `pymdown-extensions`.
3. **CI/CD Ready**: Optimized specifically for use as a **GitHub Actions Job Container**.

## 🛠 Features

- **Base Image**: `python:3.12-alpine` (Small footprint, fast pull).
- **GHA Compatible**: Includes `bash`, `git`, `tar`, `gzip` for seamless integration with GitHub Actions steps (e.g., `actions/checkout`, `actions/upload-artifact`).
- **Dynamic Generator**: Uses an internal Python script to assemble the site configuration from multiple sources.
- **Post-processing**: Automatically handles site-dir merging and cleanup.

## 📦 Required Files

To use this builder, your workspace should typically contain:

| File | Description |
| :--- | :--- |
| `info.json` | Project metadata, navigation structure, and project-specific info. |
| `docs/` | Your Markdown content. |
| `docs/assets/extra.yml` | (Optional) Peer-level overrides/extra configuration for MkDocs. |

The builder merges these with an internal `template.yml` to produce the final `mkdocs.yml` at runtime.

## 💻 Usage

### GitHub Actions (Recommended)

You can use this image directly as a job container in your workflow:

```yaml
jobs:
  build-docs:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/raineblog/mkdocs-docker:latest
    steps:
      - name: Checkout
        uses: actions/checkout@v6

      - name: Build Documentation
        run: mkdocs-build
        
      - name: Upload Artifact
        uses: actions/upload-pages-artifact@v4
        with:
          path: ./site
```

### Local Development

Run the builder inside your project directory:

```bash
docker run --rm -v $(pwd):/app/workspace -w /app/workspace ghcr.io/raineblog/mkdocs-docker:latest mkdocs-build
```

## 🛠 Maintenance & Contributions

**Please Note:** This project is a personal toolchain maintained for my own organization's needs.

- **Status**: Active but "Low-Maintenance". I use this regularly, but I have limited capacity to review large changes.
- **Bug Reports & Corrections**: Highly welcomed! If you find a typo, a logic error in the build script, or a vulnerability, please open an issue or PR.
- **Feature Requests**: I am generally **not accepting new features** or functional requests. I prefer to keep this toolchain specialized for its current purpose to minimize maintenance overhead.

If you need a more flexible or feature-rich MkDocs environment, I recommend checking out the official [Squidfunk/mkdocs-material](https://github.com/squidfunk/mkdocs-material) image.

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
