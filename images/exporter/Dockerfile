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

RUN set -eux; \
    mkdir -p /etc/dpkg/dpkg.cfg.d; \
    cat > /etc/dpkg/dpkg.cfg.d/01-ci-nodoc <<'EOF'
path-exclude /usr/share/doc/*
path-include /usr/share/doc/*/copyright
path-exclude /usr/share/man/*
path-exclude /usr/share/groff/*
path-exclude /usr/share/info/*
path-exclude /usr/share/lintian/*
path-exclude /usr/share/linda/*
EOF

RUN set -eux; \
  cat > /etc/apt/apt.conf.d/99ci-no-translations <<'EOF'
Acquire::Languages "none";
EOF

RUN set -eux; \
  cat > /etc/apt/apt.conf.d/99ci-gzip-indexes <<'EOF'
Acquire::GzipIndexes "true";
EOF

WORKDIR /app

# 2. 引入构建工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. 安装依赖、构建并清理
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    set -ex; \
    # 安装基础工具与 Bun
    apt-get update; \
    apt-get install -y --no-install-recommends \
        bash tini tar zstd unzip git ca-certificates curl wget \
        fonts-noto-cjk fonts-noto-core fonts-wqy-zenhei fonts-liberation fonts-linuxlibertine; \
    curl -fsSL https://bun.com/install | bash; \
    # 安装运行时库 (LMDB, Image rendering)
    apt-get install -y --no-install-recommends liblmdb0; \
    # 安装临时构建依赖
    buildDeps='build-essential python3-dev libffi-dev'; \
    apt-get install -y --no-install-recommends $buildDeps; \
    # 执行 Python 依赖安装
    uv sync --locked --no-cache; \
    # 清理构建依赖与缓存
    apt-get purge -y --auto-remove $buildDeps; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    # 配置
    fc-cache -fv; \
    git config --system --add safe.directory '/__w/*'

# 4. 拷贝应用与脚本
COPY scripts/ /app/scripts/
COPY templates/ /app/templates/
COPY --chmod=755 bin/ /usr/local/bin/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/usr/local/bin/mkdocs-export"]

