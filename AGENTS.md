# Working in this repository

## Architecture

- Keep the backend a modular monolith: HTTP routes in `app/api`, validation in `app/schemas`, use cases in `app/services`, persistence mappings in `app/models`, and shared configuration/security/database code in `app/core`.
- Keep endpoint functions thin. Put business rules and transaction boundaries in services; enforce durable invariants in PostgreSQL where practical.
- Email is delivered asynchronously through the PostgreSQL outbox and `app.worker`; do not send SMTP from request handlers.
- Check `.planning/product-spec.md`, `.planning/api-spec.md`, `.planning/architecture-erd.md`, and `.planning/task-breakdown.md` before implementing a product workflow. Update `.planning/progress-tracker.md` after verified work.

## Database and tests

- PostgreSQL is required for application and test work; do not add SQLite fixtures or test dependencies.
- Test URLs belong in `.env` as `TEST_DATABASE_URL` and `CTMS_MIGRATION_TEST_DATABASE_URL`, each pointing to a disposable database whose name ends in `_test`.
- Run tests with `uv run pytest -q` after setting both PostgreSQL test URLs in `.env`. Migration verification uses the dedicated fresh migration test database; never point it at a database with user data.
- Schema changes require an Alembic migration under `alembic/versions/`. Verify fresh upgrade behavior with the migration test.
- Compose provisions the local PostgreSQL instance and initializes `ctms_test` and `ctms_migration_test` when creating a new data volume.

## Current implementation and next work

- Implemented API routes: `GET /api/v1/health`, login, password setup, and `POST /api/v1/profiles/staff`.
- Admins may create Mentors; only Super Admins may create Admins. Staff accounts remain inactive until one-time setup-link redemption.
- Setup email uses the durable outbox and the separate Compose `email-worker`, configured through SMTP environment variables. `.env.example` has placeholders; supply real local values only in ignored `.env`.
- The next planned product work is Talent application approval and onboarding, reusing the auth and outbox patterns, then cohort creation and public application intake. Confirm sequencing in `.planning/progress-tracker.md` before starting.

## Local workflow

- Install/sync dependencies with `uv sync` and start services with `docker compose up -d`.
- Apply migrations with `uv run alembic upgrade head`.
- Bootstrap the first Super Admin with `uv run python -m app.cli bootstrap-super-admin` (the command prompts for credentials and refuses a second bootstrap).
- Never commit `.env`, live SMTP credentials, JWT secrets, or real passwords. `.env.example` must remain placeholder-only.
