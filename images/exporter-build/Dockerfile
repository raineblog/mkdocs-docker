# syntax=docker/dockerfile:1
FROM ghcr.io/puppeteer/puppeteer:latest

USER root

# 1. 配置环境变量 (整合 exporter 环境变量)
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH"

# 2. 预配置 APT 优化 (来自原有实现)
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

# 3. 集成所有系统依赖与 Python 环境
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    apt-get update; \
    # 基础工具
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-dev \
        bash tini tar zstd unzip git ca-certificates curl wget \
        liblmdb0 build-essential libffi-dev ghostscript \
        fonts-noto-cjk fonts-noto-cjk-extra fonts-noto-core fonts-noto-extra \
        fonts-liberation fonts-linuxlibertine fonts-noto-color-emoji \
        fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf \
        libnss3 libxss1 libasound2 libatk-bridge2.0-0 libgtk-3-0 libgbm1 libnspr4 \
        libpango-1.0-0 libpangocairo-1.0-0 lsb-release xdg-utils \
        fonts-noto-cjk fonts-noto-cjk-extra fonts-noto-core fonts-noto-extra \
        fonts-liberation fonts-linuxlibertine \
        fonts-noto-color-emoji \
        libnss3 \
        fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 \
        libasound2 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libgbm1 \
        zstd gnupg  \
        tar make bash tini tar zstd git ca-certificates curl wget \
        gconf-service libasound2 libatk1.0-0 libc6 libcairo2 \
        libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libgconf-2-4 \
        libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 \
        libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 libxcomposite1 \
        libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 \
        libxss1 libxtst6 ca-certificates fonts-liberation libnss3 lsb-release \
        xdg-utils wget \
        xvfb gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 \
        libdbus-1-3 libexpat1 libfontconfig1 libgbm1 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 \
        libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 libx11-xcb1 libxcb1 \
        libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 libxss1 \
        libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget; \
    # 清理
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*; \
    fc-cache -fv; \
    git config --system --add safe.directory '/__w/*'

WORKDIR /app

# 4. 安装 Node 依赖
COPY package.json package-lock.json* .puppeteerrc.* ./
RUN npm ci && npx puppeteer browsers install

# 5. 安装 Python 项目依赖
RUN --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-cache

# 6. 拷贝应用代码
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY templates/ ./templates/

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["npm", "start"]
