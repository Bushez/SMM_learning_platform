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

## Course authoring foundation

Teachers create `DRAFT` courses through `/api/v1/teacher/courses`. Only `PUBLISHED` courses are
returned by `/api/v1/courses`; draft content is never exposed through learner endpoints. Publishing
is server-side validated and currently requires at least one module, lesson, and task. Course,
module, lesson, task, option, and accepted-answer schema is introduced through Alembic migrations.

## Teacher media uploads

Teachers upload JPEG, PNG, and WebP images through `POST /api/v1/media/images`. The backend reads
no more than `MAX_UPLOAD_SIZE_BYTES`, verifies the actual image format and dimensions with Pillow,
then stores the file under a generated object key in MinIO and persists only `MediaAsset` metadata.
`cover_media_id` can be set only to an asset owned by the course teacher. `MINIO_ENDPOINT` is the
internal service endpoint; `MINIO_PUBLIC_ENDPOINT` is the host placed into browser-visible signed
download URLs (use `localhost:9000` for local Compose).

## Task engine

Teachers can add lessons and author `SINGLE_CHOICE`, `MULTIPLE_CHOICE`, and `TEXT_INPUT` tasks.
Choice options may contain text, image references, or both. `POST /api/v1/learning/lessons/{lesson_id}/tasks`
returns a learner-safe model that never includes option correctness, accepted text answers, or explanations.
`POST /api/v1/learning/tasks/{task_id}/attempts` evaluates the answer on the server and persists an
attempt history record; feedback is returned only after submission. XP and streak are intentionally
added in the next phase.

## Learning progress

Start a published course with `POST /api/v1/learning/courses/{course_id}/enroll`, then obtain its
aggregate progress or ordered outline from `/progress` and `/outline`. The first lesson is unlocked;
each subsequent lesson opens only after all prior lessons in the course are complete. Completion uses
the unique `(user_id, task_id)` `user_task_progress` record, so retried correct answers do not duplicate
progress. Archived courses cannot be newly enrolled in, while existing enrolled learners may continue.

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

## VPS notes

Use one public HTTPS origin behind Caddy or another reverse proxy: route `/` to the frontend and
`/api/` to FastAPI. Do not expose PostgreSQL or Redis. Keep MinIO private unless signed media URLs
require a dedicated configured hostname. Back up PostgreSQL and MinIO volumes independently.
