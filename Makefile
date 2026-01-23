# MkDocs Docker Builder - Local Development Makefile
# This file is used within the mkdocs-docker repository to manage the builder image.

IMAGE_NAME = mkdocs-builder
TAG = latest

.PHONY: build rebuild bash clean logs help

help:
	@echo "========================================================================"
	@echo "🎨 MkDocs Builder - Local Management"
	@echo "========================================================================"
	@echo "Available commands:"
	@echo "  make build          - Build the image (standard)"
	@echo "  make rebuild        - Build the image from scratch (no cache)"
	@echo "  make bash           - Enter the container bash for builder debugging"
	@echo "  make clean          - Remove the local builder image"
	@echo "  make version        - Check tool versions inside the image"
	@echo "========================================================================"

build:
	@echo "🚀 Building $(IMAGE_NAME):$(TAG)..."
	docker build -t $(IMAGE_NAME):$(TAG) .
	@echo "✅ Build complete."

rebuild:
	@echo "♻️  Rebuilding $(IMAGE_NAME):$(TAG) without cache..."
	docker build --no-cache -t $(IMAGE_NAME):$(TAG) .
	@echo "✅ Rebuild complete."

bash:
	@echo "💻 Entering builder shell..."
	docker run --rm -it $(IMAGE_NAME):$(TAG) bash

version:
	@echo "🔍 Tool Versions:"
	@docker run --rm $(IMAGE_NAME):$(TAG) bash -c "python --version && mkdocs --version && node --version"

clean:
	@echo "🧹 Removing image $(IMAGE_NAME):$(TAG)..."
	docker rmi $(IMAGE_NAME):$(TAG) || true
