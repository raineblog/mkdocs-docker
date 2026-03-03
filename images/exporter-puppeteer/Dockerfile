# syntax=docker/dockerfile:1
FROM ghcr.io/puppeteer/puppeteer:latest

USER root


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

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false
# ENV DBUS_SESSION_BUS_ADDRESS=autolaunch:
# Setting the environment variable to ensure Puppeteer uses its downloaded browser

# Install Chromium dependencies and zstd, also Chinese fonts
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends eatmydata; \
    eatmydata apt-get update && eatmydata apt-get install -y --no-install-recommends \
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
      libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release xdg-utils wget && \
    rm -rf /var/lib/apt/lists/*

# Note: We install dependencies globally or within the app directory
WORKDIR /app
COPY package.json package-lock.json* .puppeteerrc.* ./
RUN npm ci && npx puppeteer browsers install

COPY src/ ./src/

CMD ["npm", "start"]
