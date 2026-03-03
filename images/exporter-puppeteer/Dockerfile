# syntax=docker/dockerfile:1
FROM node:lts

# Install Chromium dependencies and zstd, also Chinese fonts
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-noto-color-emoji \
    fonts-liberation \
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
RUN npm install

COPY src/ ./src/

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=false
# Setting the environment variable to ensure Puppeteer uses its downloaded browser

CMD ["npm", "start"]
