# Visual learning platform

Production-minded learning platform for photography, visual design, and typography. The product
uses short visual exercises, immediate feedback, progression, XP, streaks, and leaderboards.

Phase 1 provides the runnable architecture foundation: FastAPI, Next.js, PostgreSQL, Redis,
MinIO, Docker, OpenAPI export/codegen, tests, linting, typed settings, structured request logs,
health checks, and the first visual product surface.

## Stack

- Backend: Python, FastAPI, async SQLAlchemy, Alembic, PostgreSQL, Redis, MinIO, uv.
- Frontend: Next.js App Router, React, TypeScript strict, Tailwind CSS, shadcn/Base UI,
  TanStack Query, React Hook Form, Zod, Orval, Vitest.
- Delivery: Docker Compose now; a same-origin HTTPS reverse proxy on a VPS later.

See [docs/architecture.md](docs/architecture.md) for boundaries and security decisions.

## Prerequisites

- Docker Desktop with Compose, or Python 3.12.x, uv, Node.js 24+, and pnpm 11.
- On Windows PowerShell, use `pnpm.cmd` if script execution blocks `pnpm.ps1`.

## Environment

Copy `.env.example` to `.env` for local overrides. Values are development-only. Production startup
rejects the documented placeholder JWT and MinIO secrets and requires secure refresh cookies.

## Run everything with Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- MinIO Console: http://localhost:9001

Persistent named volumes retain PostgreSQL, Redis, and MinIO data. Stop without deleting data:

```bash
docker compose down
```

## Run application processes locally

Start dependencies only:

```bash
docker compose up -d postgres redis minio minio-init
uv sync --locked
cd backend
uv run uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

## Database migrations

```bash
cd backend
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "describe change"
```

Application code must not use `Base.metadata.create_all()` as a migration mechanism.

## Authentication

`POST /api/v1/auth/register` always creates a `USER`. Login returns a short-lived access JWT in
the response and creates a rotating opaque refresh session in an HttpOnly cookie. The frontend
keeps the access token in runtime memory only.

Promote an existing user only through the local management command:

```bash
cd backend
uv run python scripts/promote_teacher.py learner@example.com
```

There is intentionally no public API route for role promotion.

## Quality commands

```bash
uv run ruff check backend
uv run ruff format --check backend
uv run mypy backend/app
uv run pytest backend/tests

cd frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
```

## OpenAPI and frontend generation

```bash
cd backend
uv run python scripts/export_openapi.py
cd ../frontend
pnpm generate-api
```

`openapi.json` is generated from FastAPI. Files under `frontend/src/shared/api/generated` are
generated artifacts and must not be edited manually.

## Upcoming management commands

The authentication phase will add an idempotent `promote_teacher <email>` command and development
seed command. There will be no public role-promotion endpoint. Seed credentials will remain
explicitly development-only.

## VPS notes

Use one public HTTPS origin behind Caddy or another reverse proxy: route `/` to the frontend and
`/api/` to FastAPI. Do not expose PostgreSQL or Redis. Keep MinIO private unless signed media URLs
require a dedicated configured hostname. Back up PostgreSQL and MinIO volumes independently.
