# syntax=docker/dockerfile:1
FROM python:slim

# 1. 配置 UV 环境变量
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHON_GIL=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# 2. 安装底层系统依赖
# 使用 apt-get 替代 apk，并补全 weasyprint 和 fonts 的 Debian 包名
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    make bash tini tar zstd \
    git ca-certificates curl wget \
    nodejs npm \
    # 字体支持
    fonts-noto-cjk fonts-noto-core fonts-wqy-zenhei fonts-liberation fonts-linuxlibertine \
    # LMDB 支持 (runtime)
    liblmdb0 libffi-dev python-dev build-essential \
    && fc-cache -fv && \
    git config --system --add safe.directory /__w/* && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. 引入构建工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 5. 安装 Python 依赖 
RUN --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-cache
ENV PATH="/app/.venv/bin:$PATH"

# 6. 拷贝应用与脚本
COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-export"]
