# syntax=docker/dockerfile:1
FROM python:slim

# 1. 配置环境变量
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHON_GIL=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    BUN_INSTALL=/usr/local \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH"

WORKDIR /app

# 2. 引入构建工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. 安装底层系统依赖、Bun 与构建环境
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -ex; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        bash tini tar zstd git openssh-client ca-certificates curl wget \
        # 图像与渲染依赖 (运行时及其开发依赖) - 遵从用户指示保留
        pngquant zlib1g-dev libcairo2-dev libfreetype6-dev libffi-dev libjpeg-dev libpng-dev libz-dev \
        # LMDB 运行时
        liblmdb0; \
    curl -fsSL https://bun.com/install | bash; \
    # 配置 Git
    git config --system --add safe.directory '/__w/*'

# 4. 安装 Node.js 依赖 (Bun)
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=bun.lock,target=bun.lock \
    --mount=type=cache,target=/root/.bun/install/cache \
    bun install --frozen-lockfile

# 5. 安装 Python 依赖并清理构建工具
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    set -ex; \
    # 安装临时构建依赖 (用于编译 lmdb 等)
    buildDeps='build-essential python3-dev'; \
    apt-get update; \
    apt-get install -y --no-install-recommends $buildDeps; \
    # 执行同步
    uv sync --locked --no-cache; \
    # 卸载构建依赖并清理
    apt-get purge -y --auto-remove $buildDeps; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# 6. 拷贝应用与脚本
COPY gulpfile.js .
COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-build"]

