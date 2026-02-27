# MkDocs Docker Toolchain

[![Docker Image Build](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/raineblog/mkdocs-docker/actions/workflows/docker-publish.yml)
[![Container Registry](https://img.shields.io/badge/Container-GHCR-blue?logo=github)](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)](https://www.python.org/)

这是一个专为现代文档工作流设计的**集成化容器构建环境**。本项目提供了一系列预配置的镜像，旨在简化文档的编写、构建与发布流程，特别针对 **GitHub Actions** 进行了极致优化。

> [!IMPORTANT]
> **项目定位**：本项目是一个个人维护的工具链。我欢迎错误报告 (Bug Reports) 和文档修正，但我目前没有精力处理新的功能请求 (Feature Requests)。

---

## 🌟 核心特性

- 🚀 **极速构建**：基于 Alpine Linux，镜像体积小（~50MB），冷启动与拉取速度极快。
- 🧩 **动态配置 (Config-as-Data)**：无需手动维护复杂的 `mkdocs.yml`，系统会根据 `info.json` 自动生成。
- 🔋 **开箱即用**：集成了常用的 MkDocs 插件（如亮箱效果、HTML 压缩、数学公式支持等）。
- 🛠 **CI/CD 优化**：内置 `git`、`nodejs`、`markdownlint` 等工具，完美适配主流流水线。
- 📦 **多镜像支持**：除了核心的 `mkdocs` 镜像，还包含 `rspress`、`exporter` 和 `seo` 等专用镜像。

---

## 🗂 目录树预览

| 目录/文件 | 描述 |
| :--- | :--- |
| `images/mkdocs/` | 核心 MkDocs 镜像定义，包含构建与预览脚本 |
| `images/rspress/` | Rspress 相关镜像定义 |
| `images/exporter/` | 专门用于将文档导出为其他格式（如 PDF）的镜像 |
| `images/seo/` | 网站 SEO 优化辅助工具 |
| `shared/` | 跨镜像共享的资源或脚本 |

---

## 🚀 快速开始

### 1. 拉取镜像

```bash
docker pull ghcr.io/raineblog/mkdocs-docker:latest
```

### 2. 本地构建文档

在包含 `docs/` 和 `info.json` 的项目根目录下运行：

```bash
docker run --rm -v $(pwd):/app/workspace -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest mkdocs-build
```

### 3. 本地实时预览

```bash
docker run --rm -it -p 8000:8000 -v $(pwd):/app/workspace -w /app/workspace \
  ghcr.io/raineblog/mkdocs-docker:latest mkdocs-serve
```

---

## ⚙️ 核心配置：info.json

该项目采用“配置即数据”的理念。你只需要提供一个简单的 `info.json`，构建环境会自动合并模板生成最终的 `mkdocs.yml`。

### 示例 `info.json`

```json
{
  "project": {
    "site_name": "我的文档项目",
    "site_description": "基于 MkDocs Docker 的示例项目",
    "repo_url": "https://github.com/your-username/your-repo"
  },
  "nav": [
    {
      "title": "指南",
      "children": ["guide/index.md", "guide/usage.md"]
    }
  ]
}
```

---

## 🛠 可用指令

在 `mkdocs` 镜像中，你可以直接调用以下封装好的 CLI 命令：

| 命令 | 描述 |
| :--- | :--- |
| `mkdocs-build` | 完整流水线：Lint 校验 -> 配置生成 -> 生产环境构建 |
| `mkdocs-serve` | 启动开发服务器，支持热重载（端口 8000） |
| `mkdocs-lint` | 启动 `markdownlint` 进行文档规范检查并尝试自动修复 |

---

## 🤝 贡献说明

本项目由 [@raineblog](https://github.com/raineblog) 维护。虽然它是一个个人工具，但我非常高兴收到社区的反馈。

- **🐛 缺陷反馈**：如果你发现了代码或文档中的 Bug，请提交 Issue。
- **📝 文档修正**：欢迎针对错别字或表述不清的地方提交 PR。
- **✨ 功能建议**：**通常不被接受**。建议 fork 本项目或使用官方镜像以满足个性化需求。

---

## 📄 许可证

本项目采用 [MIT License](LICENSE) 开源。

---

<div align="center">

**[镜像库](https://github.com/raineblog/mkdocs-docker/pkgs/container/mkdocs-docker)** · **[提交 Bug](https://github.com/raineblog/mkdocs-docker/issues)** · **[查看源码](https://github.com/raineblog/mkdocs-docker)**

</div>

---

<sub>
📝 **文档说明**：本文件由人工智能 **Antigravity (model: Claude 3.5 Sonnet)** 根据项目结构自动生成，并已经过人工确认与验收。
</sub>
