# TimeTrack — Architecture

A condensed map of the moving parts. Code is the source of truth; this is
context that isn't obvious from reading any single file.

## Stack at a glance

```
┌──────────────────────────┐    HTTP/JSON      ┌──────────────────────────────┐
│ React 19 + Vite 6        │ ─────────────────▶│ Flask 3.1 app factory        │
│ TanStack Query / Router  │  /api/v1/*        │ Blueprints (thin)            │
│ Tailwind v4 + shadcn/ui  │ ◀─────────────────│ Pydantic 2 boundary schemas  │
└──────────────────────────┘                   │ Services (framework-free)    │
                                               │ SQLAlchemy 2.0 typed models  │
                                               └──────────────┬───────────────┘
                                                              │
                                                       Postgres 16
```

Three test tiers, all sharing the same Postgres test database:

- **Unit** (`backend/tests/unit/`) — service-level, no app context. Pure functions.
- **Integration** (`backend/tests/integration/`) — boot Flask, hit endpoints, assert on JSON + DB state. Default tier; most coverage lives here.
- **E2E** (`backend/tests/e2e/`) — Playwright Python driving Chromium against a built frontend served by Flask in a thread. One process; one DB; cleared between tests via `/api/v1/test/reset`.

## Timer model — server-authoritative event log

`time_entries` and `timer_events` together encode timer state. Duration is **computed** from events, not derived from `now() - started_at`:

```
POST /timer/start  → creates entry + (START)
POST /timer/pause  → appends (PAUSE)
POST /timer/resume → appends (RESUME)
POST /timer/stop   → appends (STOP); ended_at = now;
                     duration_seconds = sum(active spans);
                     rounded_seconds = ceil(duration / rounding_unit) * rounding_unit
```

`compute_elapsed_seconds(events, as_of)` walks the events list, pairing each
START/RESUME with the next PAUSE/STOP. The trailing span (no closing event)
runs to `as_of` — that's what `GET /timer/current` returns for the client's UI tick.

A user has at most one *open* entry at a time (`ended_at IS NULL`). Calling
start while one exists returns `409 Conflict`.

The frontend polls `/timer/current` on focus + every 30 s and ticks elapsed
seconds locally between polls; the server remains the source of truth on
reconnect.

## Approval state machine

Statuses live in the `entry_status` enum on `time_entries.status`:

```
       owner               manager
draft  ────▶  submitted  ─────▶  approved  ───▶  invoiced
   ▲                         │
   └──── reject (manager) ───┘   (reason appended to notes)
```

Transitions are enforced in `entry_service.submit_entries` /
`approve_entries` / `reject_entries`. The blueprint layer never mutates state
directly — it parses, delegates, serializes.

`invoiced` entries are read-only until the invoice is voided
(`invoice_service.void` flips them back to `approved` and clears
`invoice_id`).

## Invoicing logic

Eligibility: `status = approved AND invoice_id IS NULL` AND
`started_at ∈ [start_date, end_date]` AND `project.client_id = client_id`.

Line grouping: per (project, user). Within a group:

- `seconds = sum(rounded_seconds or duration_seconds)` per entry
- `hours = seconds / 3600`
- `rate_cents = member.rate_override_cents ?? project.default_rate_cents ?? user.default_hourly_rate_cents ?? 0`
- `amount_cents = floor(hours * rate_cents)`

Subtotal is sum of line amounts. Total = `subtotal * (1 + tax_rate)`.
Single `tax_rate` per invoice (Decimal, 0–1).

Invoice numbers are globally sequential: `INV-{YYYY}-{0001..}` via a tiny
single-row `invoice_counter` table acquired with `SELECT … FOR UPDATE` so
parallel creates don't race.

PDFs render through WeasyPrint when its native libraries are installed (Pango,
Cairo, GDK-PixBuf — provided by the Docker image's `apt` step). On systems
missing those libs, `invoice_service.render_pdf` falls back to a one-line
`%PDF-1.4` placeholder so the file exists for download in dev.

## Money

Integer **cents** in the DB. `Decimal` in Python for tax math. Format on the
client (`formatCents` uses `Intl.NumberFormat`). Never `float`.

## Auth

- Argon2id for passwords (`app.services.auth_service.hash_password`).
- JWT access 15 min, refresh 7 days, refresh rotation: each refresh revokes
  the presented JTI and issues a new pair. Revocations live in
  `revoked_tokens`; the JWT-Extended blocklist loader checks every protected
  request.
- Bootstrap: the first POST to `/auth/register` (no DB users) is admin; every
  subsequent register requires an admin JWT.
- `@require_role(Role.ADMIN, …)` decorator wraps mutating endpoints; ownership
  re-checks happen inside service functions (no trusting the route alone).

## Frontend testing strategy

| Tier              | What it proves                                            |
| ----------------- | --------------------------------------------------------- |
| Vitest / RTL      | Components render the right thing for given props/state. |
| Backend integration | The HTTP contract — what real callers see and store.   |
| Playwright        | The user can actually accomplish each named flow.       |

Mocking only at trust boundaries: the clock (when tests need it), outbound
HTTP, the filesystem. Postgres is **not** a trust boundary — every integration
and e2e test hits a real DB so the SQL we ship is the SQL we cover.

Per-test isolation: integration tests autouse `_isolate_db` to `DELETE FROM`
every table after each test. E2E tests autouse `_reset_between_tests` which
POSTs `/api/v1/test/reset` (registered only when `TESTING=True`).

## Repo conventions

- `services/` is framework-free: no Flask imports. Take models in, return
  models / value objects out. That's how unit tests can call them without an
  app context.
- Blueprints in `api/` are thin: parse Pydantic → call service → serialize
  Pydantic → jsonify. ~60 lines each.
- Pydantic at boundaries only. SQLAlchemy models persist. Value objects in
  services are `@dataclass(frozen=True, slots=True)` (none added yet — pattern
  reserved for future complexity).
- Module-level error classes in `app/errors.py`; each carries a stable `code`
  and HTTP `status`. The error handler converts them to the
  `{"error": {"code", "message", "details"}}` envelope.

## Things deliberately deferred past v1

- Multi-currency UI (schema is currency-aware; only USD shown).
- Email (Resend/SES) — `POST /invoices/:id/send` only flips status, doesn't
  send.
- Stripe payment links.
- File-based TanStack Router (code-based for now; migrating later is a one-time
  task).
- Optimistic mutations in the UI (server round-trip is fast enough today).
- Skeleton loaders (`isLoading` checks render "Loading…" inline).
