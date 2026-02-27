# MkDocs Docker Toolchain 🚀

[![Docker Image Build](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml)
[![Container Registry](https://img.shields.io/badge/Container-GHCR-blue?logo=github)](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Uv](https://img.shields.io/badge/managed%20by-uv-261230?style=flat&logo=python&logoColor=white)](https://github.com/astral-sh/uv)

这是一个专门为现代文档工作流设计的**全栈式容器化工具链**。本项目通过一系列高度优化的镜像，覆盖了从文档编写、实时预览、静态构建到多格式导出及 SEO 优化的全生命周期。

> [!IMPORTANT]
> **项目定位**：本项目是一个个人维护的专业工具集。我欢迎 Bug 反馈和文档改进建议，但出于精力考虑，**不接受新的功能请求 (Feature Requests)**。如果您有特殊需求，建议 fork 本项目自行定制。

---

## 🏗 工具链概览

本项目包含 5 个核心镜像，各司其职，共同构成完整的文档构建生态：

| 镜像名称 | 职责描述 | 核心技术栈 |
| :--- | :--- | :--- |
| **`mkdocs`** | 核心构建与预览环境，支持动态配置生成 | Python 3.12, Node.js (PostHTML) |
| **`exporter`** | **[性能优化]** 将文档导出为 PDF 等格式 | **uv**, WeasyPrint, TeX Live |
| **`rspress`** | 基于 Rspress 的极速静态站点生成 | Node.js, Rspress |
| **`fragment`** | 专门用于生成“片段化”或特定格式的 MkDocs 文档 | Python, Pandoc |
| **`seo`** | 自动化 SEO 优化与搜索引擎推送工具 | Python (Requests) |

---

## ✨ 核心亮点

- ⚡ **性能极致优化**：部分镜像（如 `exporter`）已全面引入 `uv` 管理依赖，构建与运行速度提升显著。
- 🧩 **配置即数据 (Config-as-Data)**：告别手动编写数千行的 `mkdocs.yml`。通过 `info.json` + 预定义模板，自动生成生产级的配置文件。
- 🎨 **高度定制化插件**：内置了 `mkdocs-katex-ssr`、`mkdocs-glightbox` 以及作者定制的 `mkdocs-material` 分支，确保文档既专业又美观。
- 🔗 **CI/CD 原生支持**：深度适配 GitHub Actions，提供开箱即用的自动化部署体验。

---

## 🚀 快速开始

### 核心镜像：MkDocs

#### 1. 实时预览 (Hot Reload)
```bash
docker run --rm -it -p 8000:8000 \
  -v $(pwd):/app/workspace -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest mkdocs-serve
```

#### 2. 生成环境构建
```bash
docker run --rm -v $(pwd):/app/workspace -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest mkdocs-build
```

### 性能之选：Exporter (使用 uv)

导出 PDF 的极速方案：
```bash
docker run --rm -v $(pwd):/app/workspace -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker/exporter:latest mkdocs-export
```

---

## ⚙️ 核心逻辑：info.json

该工具链的核心在于通过 `info.json` 驱动。它定义了项目的元数据、导航结构及扩展配置。

```json
{
  "project": {
    "site_name": "文档名称",
    "site_description": "文档描述",
    "repo_url": "https://github.com/user/repo"
  },
  "nav": [
    {
      "title": "开始",
      "children": ["index.md", "usage.md"]
    }
  ]
}
```

---

## 🛠 维护与贡献

本项目由 [@raineblog](https://github.com/raineblog) 持久维护以满足自身工作流。

- **反馈问题**：请通过 [GitHub Issues](https://github.com/raineblog/mkdocs-docker/issues) 提交。
- **参与贡献**：仅接受 Bug Fix 或 文档润色。
- **重构记录**：项目近期完成了从单体架构向多镜像组合的彻底重构，并开始引入 `uv` 等高性能工具。

---

## 📄 许可证

基于 [MIT License](LICENSE) 开源。

---

<div align="center">

**[GitHub Container Registry](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)** · **[报告 Bug](https://github.com/raineblog/mkdocs-docker/issues)**

</div>

---

<sub>
📝 **文档说明**：本文件由人工智能 **Antigravity (model: Claude 3.5 Sonnet)** 深度分析重构后的项目结构后自动生成，并已经过人工确认与验收。
</sub>
