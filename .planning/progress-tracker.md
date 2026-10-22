# CTMS Progress Tracker

Last reviewed: 2026-10-22

## Current state

The repository is at an early backend scaffold stage. Product, ERD, API, and work-plan documentation exist in `docs/`; API v1 routing is wired, with the versioned health route verified. The application package contains model/schema/service/endpoint module files, but most product API behavior described in the contract is not yet implemented.

Verified implementation observations:

- [x] FastAPI app exposes `GET /api/v1/health` returning `{"status":"ok"}`.
- [x] Python package and core modules exist for configuration, database setup, security, models, schemas, services, and endpoint modules.
- [x] `uv` project metadata and lockfile are present; the project requires Python 3.12+.
- [x] Pytest baseline exists; five tests pass, including database constraint tests against SQLite.
- [x] Alembic is configured with an initial schema migration. Offline SQL generation was verified for PostgreSQL.
- [x] API v1 routers are registered by `app/api/v1/api.py`.
- [ ] Product API endpoints beyond health are not implemented.
- [x] Initial migration applied successfully to a fresh local PostgreSQL 16 database. An opt-in PostgreSQL migration test checks its tables and revision, then downgrades the disposable test database.
- [x] Dockerfile defines the API image; Docker Compose defines PostgreSQL 16 with a persistent volume and health check. Compose startup and migration were verified locally.
- [x] One-time Super Admin CLI refuses a second bootstrap and serializes concurrent bootstrap attempts with a PostgreSQL advisory lock.
- [x] Opt-in PostgreSQL migration test verifies the fresh schema and revision, then downgrades the disposable test database.
- [ ] No formatter, linter, type checker, or CI workflow is configured.
- [ ] Public widget, email integration, and the documented application-to-chat lifecycle are not implemented.

The checked source currently proves the versioned health endpoint as a working HTTP behavior. Presence of model/service/schema module files is not evidence that their intended business workflows are complete.

## Model/contract comparison findings

- Application and Profile models have several useful status/role checks, and Conversation models enforce the general-vs-track target shape and uniqueness per cohort/track.
- Application uniqueness is now enforced by a unique index on trimmed, lowercased email plus cohort. The intake service must still normalize the value before persistence when implemented.
- Application and Profile now use composite foreign keys to ensure the selected Track belongs to the referenced Cohort.
- The models do not yet include setup-token or email-outbox persistence.
- The API contract says cohort creation is Admin/Super Admin; post-creation track creation is now recorded with the same role rule.

## Documentation completed

- [x] Read and summarized the product overview, ERD, API contract, and work plan.
- [x] Compared the current SQLAlchemy model definitions with the documented ERD/API.
- [x] Reconciled documented behavior with the current scaffold; documented remaining model/contract gaps above.
- [x] Recorded agreed MVP policies: single cohort/track assignment per Talent Profile, durable email outbox, 24-hour single-use setup tokens, 15-minute JWTs without refresh, and Admin/Super Admin track creation.
- [x] Created a product requirements reference in [`01-product-spec.md`](./01-product-spec.md).
- [x] Created the architecture and ERD reference in [`02-architecture-erd.md`](./02-architecture-erd.md).
- [x] Created the endpoint/schema summary in [`03-api-spec.md`](./03-api-spec.md).
- [x] Created the granular implementation checklist in [`04-task-breakdown.md`](./04-task-breakdown.md).
- [x] Recorded the confirmed stack and current engineering constraints in [`coding-rules.md`](./coding-rules.md).
- [x] Added focused model-constraint tests, Alembic environment/configuration, and the initial migration.

## Contract decisions confirmed

- Talent Profiles have one cohort and track assignment at a time. A second approval for an existing Profile email conflicts; multi-cohort enrollment is out of MVP scope.
- Approval, inactive Profile creation, and a durable email-outbox event are atomic. Email delivery retries independently.
- Talent and onboarded Staff setup tokens are single-use and expire after 24 hours.
- Access JWTs expire after 15 minutes; the MVP does not include refresh tokens.
- Admins/Super Admins can create tracks after cohort creation. Staff may list profiles subject to server-enforced permission scoping.
- Bootstrap the first Super Admin through a one-time CLI command that refuses to run if one already exists; do not expose a public bootstrap endpoint.
- Newly onboarded Admin/Mentor Profiles remain inactive until they complete the same one-time password-setup flow as Talents.

## Remaining contract decisions

- Production email provider and retry/operations configuration.
- Widget hosting, embed snippet, CORS/origin rules, and supported browsers.
- Deployment/CI provider, consistent error envelope, and complete list/pagination schemas.
- Detailed per-role filter/result scoping for profile listing.

## Recommended next steps

1. Normalize application email in the intake service.
2. Implement shared request/authorization behavior.
3. Deliver authentication and cohort/application lifecycle before messaging.
4. Add the widget and complete integration/release checks.

See [`04-task-breakdown.md`](./04-task-breakdown.md) for the complete checklist and [`docs/work-plan.md`](../docs/work-plan.md) for the original phase plan.

## Maintenance

Update this file whenever meaningful work is completed. Mark items done only after verification (tests, migration checks, or a reproducible manual check as appropriate). Keep planned requirements separate from verified implementation facts.
