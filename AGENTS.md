# Project operating guide

- Preserve the modular-monolith boundary: Presentation -> Application -> Domain. Infrastructure
  implements inward-defined ports; Domain never imports FastAPI, SQLAlchemy, Redis, S3, or Pydantic HTTP schemas.
- Keep routers thin and business rules in domain/application code. Centralize current-user,
  role, and resource-ownership authorization dependencies.
- Never expose correct answers from learner task endpoints. Teacher correctness data requires
  both `TEACHER` role and course ownership. Registration never accepts a role.
- Every database schema change requires an Alembic migration; do not use `create_all()`.
- Use Python 3.12.x only. Keep Ruff and mypy configured for Python 3.12 and CI on the same version.
- Use timezone-aware UTC timestamps, UUID public IDs, and database uniqueness for XP/session/activity idempotency.
- Frontend business state comes from FastAPI. Use TanStack Query for server state and React Hook Form for forms.
- Keep UI strings in `frontend/messages/ru.json`, colors in semantic CSS tokens, and the temporary name in site config.
- Do not edit `frontend/src/shared/api/generated` by hand. Export OpenAPI, then run `pnpm generate-api`.
- Before handoff run backend Ruff, myPy, pytest; frontend lint, typecheck, tests, and production build.
- Main commands: `docker compose up --build`, `docker compose down`, `uv sync --locked`,
  `cd backend && uv run alembic upgrade head`, `cd frontend && pnpm install --frozen-lockfile`.
