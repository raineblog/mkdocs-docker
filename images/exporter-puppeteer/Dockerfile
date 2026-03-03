# syntax=docker/dockerfile:1
FROM ghcr.io/puppeteer/puppeteer:latest

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false
# Setting the environment variable to ensure Puppeteer uses its downloaded browser

# Install Chromium dependencies and zstd, also Chinese fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-noto-cjk fonts-noto-cjk-extra fonts-noto-core fonts-noto-extra \
    fonts-liberation fonts-linuxlibertine \
    fonts-noto-color-emoji \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    zstd \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Note: We install dependencies globally or within the app directory
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

COPY src/ ./src/

CMD ["npm", "start"]
