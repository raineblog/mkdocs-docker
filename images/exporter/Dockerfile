# syntax=docker/dockerfile:1
FROM python:alpine

# 1. 配置 UV 环境变量 (移除冲突的 UV_SYSTEM_PYTHON=1)
ENV UV_COMPILE_BYTECODE=1 \
    UV_NO_DEV=1 \
    UV_LINK_MODE=copy

# 2. 安装底层系统依赖 (耗时最长、变动最少，置于最前以最大化层缓存)
# 合并了后续的 git config，减少构建层数，压缩最终体积
RUN apk add --no-cache \
    bash tini tar zstd \
    git git-fast-import \
    ca-certificates curl wget \
    weasyprint \
    so:libgobject-2.0.so.0 so:libpango-1.0.so.0 so:libharfbuzz.so.0 so:libharfbuzz-subset.so.0 so:libfontconfig.so.1 so:libpangoft2-1.0.so.0 \
    font-liberation font-liberation-sans-narrow ttf-linux-libertine \
    fontconfig texlive-full \
    && fc-cache -fv \
    && git config --system --add safe.directory /__w/*

# 3. 引入构建工具 (uv:latest 标签更新频繁，需置于底层系统依赖之后)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# 5. 安装 Python 依赖 
# - 使用 BuildKit bind 挂载，不产生额外的 COPY 镜像层
# - 结合 uv 缓存挂载，提升重复构建速度
RUN --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
ENV PATH="/app/.venv/bin:$PATH"

# 6. 拷贝应用与脚本 (变动最为频繁的代码与脚本，置于末尾)
COPY scripts/ /app/scripts/
COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-export"]