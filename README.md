# TimeTrack

Time tracking & invoicing SPA for small consulting/agency teams.

**Stack:** Flask 3.1 + SQLAlchemy 2.0 (typed) + Pydantic 2 + Postgres 16 / React 19 + Vite 6 + TanStack + Tailwind v4 / Playwright e2e.

## Prerequisites

- **Docker Desktop** (running Postgres locally and for the production-parity build)
- **Python 3.12+** locally (we pin 3.13 in Docker; spec target). `uv` manages the venv.
- **Node 24+**
- **just** — task runner (`winget install Casey.Just`)
- **uv** — Python package manager (`winget install astral-sh.uv`)

> _Why `just` and not `make`?_ `make` isn't installed on Windows by default and `just` is cross-platform with a cleaner syntax. The spec allowed either. If you prefer make, the recipes translate one-to-one.

## First-time setup

```powershell
just install            # backend deps via uv + frontend deps via npm
just playwright-install # install Chromium for e2e
just db-up              # start Postgres in Docker
```

## Daily loop

```powershell
just db-up              # ensure Postgres is running
just dev-backend        # in one terminal — Flask on :5000
just dev-frontend       # in another — Vite on :5173 (proxies /api -> :5000)
```

Or fully Dockerized (matches CI exactly, slower iteration):

```powershell
just dev-docker
```

## Testing

Three tiers, each runnable independently:

```powershell
just test               # backend unit + integration (pytest)
just test-frontend      # component tests (Vitest)
just test-e2e           # end-to-end (Playwright)
just test-all           # everything
```

## Quality gates

```powershell
just lint               # ruff + eslint
just typecheck          # mypy strict + tsc
just format             # ruff format/fix
```

## Project layout

```
timetrack/
├── backend/        # Flask app, models, services, blueprints, pytest + Playwright tests
├── frontend/       # React + Vite app, Vitest tests
├── infra/db/init/  # First-boot SQL for the Postgres container (creates test DB)
├── docker-compose.yml
├── justfile
└── README.md
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the timer model, approval state machine, invoicing logic, and testing strategy.

## Phase status

- [x] Phase 1 — scaffold + health endpoint
- [x] Phase 2 — auth (users, JWT, login, /me, protected routes, seeded admin)
- [x] Phase 3 — clients & projects (CRUD + admin screens)
- [x] Phase 4 — time entries + timer (server-authoritative event log)
- [x] Phase 5 — timesheet (week grid + submit)
- [x] Phase 6 — approvals (manager bulk approve/reject)
- [x] Phase 7 — invoicing (preview/create/PDF/send/paid/void)
- [x] Phase 8 — reports (utilization / revenue / outstanding)
- [x] Phase 9 — polish (idle modal, spacebar shortcut, error boundary)

## Demo data

Once Postgres is up and migrations are applied:

```powershell
just seed
```

Creates the demo accounts below. All passwords are `demo-password`.

| Role     | Email                  |
| -------- | ---------------------- |
| admin    | admin@timetrack.dev    |
| manager  | manager@timetrack.dev  |
| employee | dev1@timetrack.dev     |
| employee | dev2@timetrack.dev     |

Plus two clients, three projects with rate overrides, ~10 days of varied
entries (mix of draft / submitted / approved), and one draft invoice.

## Environment variables

| Variable           | Purpose                                          | Default                      |
| ------------------ | ------------------------------------------------ | ---------------------------- |
| `FLASK_ENV`        | `development` \| `test` \| `production`          | `development`                |
| `DATABASE_URL`     | Primary Postgres connection                      | local Docker postgres        |
| `TEST_DATABASE_URL`| Test DB connection (used when `FLASK_ENV=test`)  | local Docker postgres `_test`|
| `SECRET_KEY`       | Flask session secret                             | dev value (override in prod) |
| `JWT_SECRET_KEY`   | JWT signing key                                  | dev value (override in prod) |
