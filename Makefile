# DotMac Platform - primary helpers (platform stack only)

SHELL := /bin/bash

CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

.PHONY: help start-infra stop-infra start-platform stop-platform start-all stop-all status logs clean build-backend build-worker

help:
	@echo "$(CYAN)DotMac Platform targets$(NC)"
	@echo "  make start-infra     Start shared infra (docker-compose.infra.yml)"
	@echo "  make stop-infra      Stop shared infra"
	@echo "  make start-platform  Start backend + admin UI (docker-compose.base.yml)"
	@echo "  make stop-platform   Stop backend + admin UI"
	@echo "  make start-all       Start infra + platform + worker"
	@echo "  make stop-all        Stop infra + platform + worker"
	@echo "  make status          docker compose ps for platform stack"
	@echo "  make logs            Tail platform stack logs"
	@echo "  make clean           Down platform + infra stacks (keeps volumes)"
	@echo "  make build-backend   Build backend image from Dockerfile"
	@echo "  make build-worker    Build worker image from Dockerfile.prod (celery stage)"

start-infra:
	docker compose -f docker-compose.infra.yml up -d

stop-infra:
	docker compose -f docker-compose.infra.yml down

start-platform:
	docker compose -f docker-compose.base.yml up -d

stop-platform:
	docker compose -f docker-compose.base.yml down

start-all:
	docker compose -f docker-compose.infra.yml up -d
	docker compose -f docker-compose.base.yml up -d
	docker compose -f docker-compose.prod.yml up -d

stop-all:
	docker compose -f docker-compose.prod.yml down || true
	docker compose -f docker-compose.base.yml down || true
	docker compose -f docker-compose.infra.yml down || true

status:
	docker compose -f docker-compose.base.yml ps

logs:
	docker compose -f docker-compose.base.yml logs -f

clean:
	docker compose -f docker-compose.prod.yml down || true
	docker compose -f docker-compose.base.yml down || true
	docker compose -f docker-compose.infra.yml down || true

build-backend:
	docker build -t dotmac-platform-backend -f Dockerfile .

build-worker:
	docker build -t dotmac-platform-worker --target celery -f Dockerfile.prod .
