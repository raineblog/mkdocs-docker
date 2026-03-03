# syntax=docker/dockerfile:1
FROM python:slim

# 1. 配置 UV 环境变量
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHON_GIL=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 2. 安装底层系统依赖
# 对应原 alpine 镜像依赖并迁移至 Debian 语法，添加 lmdb 和编译环境
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    make bash tini tar zstd \
    git openssh-client ca-certificates curl wget \
    nodejs npm \
    # 编译与工具依赖 (对应 libffi-dev python-dev build-essential)
    build-essential python3-dev libffi-dev \
    # 图像与渲染依赖 (对应 alpine 的 zlib-dev cairo freetype-dev jpeg-dev pngquant)
    zlib1g-dev libcairo2-dev libfreetype6-dev libjpeg-dev pngquant \
    libcairo2-dev libfreetype6-dev libffi-dev libjpeg-dev libpng-dev libz-dev \
    # LMDB 支持
    liblmdb0 \
    && npm install -g bun && \
    git config --system --add safe.directory /__w/* && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. 引入构建工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 4. 安装 Node.js 依赖 (Bun)
RUN --mount=type=bind,source=package.json,target=package.json \
    --mount=type=bind,source=bun.lock,target=bun.lock \
    --mount=type=cache,target=/root/.bun/install/cache \
    bun ci

# 5. 安装 Python 依赖 
RUN --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-cache
ENV PATH="/app/.venv/bin:$PATH"

# 6. 拷贝应用与脚本
COPY gulpfile.js .
COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-build"]
