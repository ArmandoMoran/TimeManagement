# TimeTrack — task runner. Run `just` to list recipes.
# Requires: just, uv, docker, node 24+.

set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]
set shell := ["bash", "-cu"]

# Defaults
backend := "backend"
frontend := "frontend"

# ---------- meta ----------

default:
    @just --list

# ---------- bootstrap ----------

install: install-backend install-frontend

install-backend:
    cd {{backend}} && uv sync --extra dev

install-frontend:
    cd {{frontend}} && npm install

# ---------- dev ----------

# Run Postgres (Docker), Flask (native), Vite (native) — recommended local loop.
dev: db-up
    @echo "Backend on :5000, frontend on :5173. Ctrl-C to stop each."

dev-backend:
    cd {{backend}} && uv run flask --app wsgi run --host 0.0.0.0 --port 5000 --debug

dev-frontend:
    cd {{frontend}} && npm run dev

# Full-stack via Docker (uses Python 3.13 in container, matches CI).
dev-docker:
    docker compose --profile docker up --build

db-up:
    docker compose up -d db

db-down:
    docker compose stop db

db-reset:
    docker compose down -v db
    docker compose up -d db

# ---------- tests ----------

# Backend pytest (unit + integration). Requires Postgres up for integration tests.
test:
    cd {{backend}} && uv run pytest -m "not e2e"

test-unit:
    cd {{backend}} && uv run pytest tests/unit

test-integration: db-up
    cd {{backend}} && uv run pytest tests/integration

# Frontend Vitest.
test-frontend:
    cd {{frontend}} && npm test

# Playwright end-to-end suite.
test-e2e: db-up
    cd {{backend}} && uv run pytest -m e2e tests/e2e

# All three tiers.
test-all: test test-frontend test-e2e

# ---------- quality ----------

lint: lint-backend lint-frontend

lint-backend:
    cd {{backend}} && uv run ruff check . && uv run ruff format --check .

lint-frontend:
    cd {{frontend}} && npm run lint

format:
    cd {{backend}} && uv run ruff format .
    cd {{backend}} && uv run ruff check --fix .

typecheck: typecheck-backend typecheck-frontend

typecheck-backend:
    cd {{backend}} && uv run mypy

typecheck-frontend:
    cd {{frontend}} && npm run typecheck

# ---------- db / migrations ----------

migrate:
    cd {{backend}} && uv run flask --app wsgi db upgrade

migration message:
    cd {{backend}} && uv run flask --app wsgi db migrate -m "{{message}}"

seed:
    cd {{backend}} && uv run python -m app.seed

# ---------- playwright ----------

playwright-install:
    cd {{backend}} && uv run playwright install chromium

# ---------- clean ----------

clean:
    cd {{backend}} && rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
    cd {{frontend}} && rm -rf dist node_modules/.vite
