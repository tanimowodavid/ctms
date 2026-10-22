# CTMS Progress Tracker

Last reviewed: 2026-10-22

## Current state

The repository has a modular FastAPI backend with versioned routing, PostgreSQL persistence, JWT authentication, staff onboarding, cohort/track management, and public application intake with a standalone widget. Application review/Talent lifecycle and messaging workflows remain unimplemented.

Verified implementation observations:

- [x] FastAPI app exposes `GET /api/v1/health` returning `{"status":"ok"}`.
- [x] Python package and core modules exist for configuration, database setup, security, models, schemas, services, and endpoint modules.
- [x] `uv` project metadata and lockfile are present; the project requires Python 3.12+.
- [x] Pytest suite uses dedicated PostgreSQL test databases; sixteen tests pass, including fresh-database migration, staff onboarding, cohort management, public application intake/CORS, and email-worker retry coverage.
- [x] Alembic is configured with an initial schema migration. Offline SQL generation was verified for PostgreSQL.
- [x] API v1 routers are registered by `app/api/v1/api.py`.
- [x] API v1 exposes health, login, password setup, staff onboarding, cohort/track endpoints, public widget options, and public application submission. Application review and messaging endpoints remain unimplemented.
- [x] Admins and Super Admins can create cohorts with at least one track; each cohort receives a unique embed token, a general conversation, and a conversation for every track in the same transaction.
- [x] Admins and Super Admins can add tracks with their track conversations. Staff can list all cohorts/tracks; Talents are scoped to their own cohort.
- [x] Cohort creation rollback, generated conversations, track creation, input validation, and role/listing scope are covered by PostgreSQL integration tests.
- [x] Public intake validates the embed token, cohort-owned track, normalized name/email, duplicate applications, and UTC start-time cutoff. The normalized-email database index handles concurrent submissions.
- [x] The standalone HTML/JavaScript application form and iframe loader fetch public track options and display loading, success, validation, duplicate, closed-intake, and network-error states.
- [x] CORS uses an exact origin allowlist from `CORS_ALLOWED_ORIGINS`; wildcard origins and credentialed requests are rejected. Intake concurrency and allowed/blocked CORS preflights are covered by integration tests.
- [x] Initial schema and staff-onboarding migrations verified against a fresh PostgreSQL 16 test database. The app database is migrated to the same head revision.
- [x] Dockerfile defines the API image; Docker Compose defines PostgreSQL 16 with a persistent volume and health check. Compose startup and migration were verified locally.
- [x] One-time Super Admin CLI refuses a second bootstrap and serializes concurrent bootstrap attempts with a PostgreSQL advisory lock.
- [x] PostgreSQL migration test verifies the fresh schema and head revision, then cleans up its disposable database.
- [x] Staff creation atomically stores an inactive Profile and email outbox event. Admins can create Mentors; Super Admins can create Admins.
- [x] Staff setup email is sent by a separate SMTP worker with capped exponential retries. Setup tokens are stored as hashes and are single-use for 24 hours.
- [x] Active Profile login issues 15-minute JWT access tokens; protected requests reload Profile status and role from PostgreSQL.
- [ ] No formatter, linter, type checker, or CI workflow is configured.
- [ ] Application review, Talent onboarding, and the documented application-to-chat lifecycle are not implemented.

The checked source and tests prove the cohort/track and public intake workflows. Other model/service/schema modules are not evidence that their intended business workflows are complete.

## Model/contract comparison findings

- Application and Profile models have several useful status/role checks, and Conversation models enforce the general-vs-track target shape and uniqueness per cohort/track.
- Application uniqueness is enforced by a unique index on trimmed, lowercased email plus cohort; the intake service normalizes email before persistence and maps concurrent conflicts to `409`.
- Application and Profile now use composite foreign keys to ensure the selected Track belongs to the referenced Cohort.
- Password setup tokens and the durable email outbox are persisted in their own tables.
- The API contract says cohort creation is Admin/Super Admin; post-creation track creation is now recorded with the same role rule.
- Cohort/track creation and listing routes follow those role and Talent cohort-scope rules. Cohort setup creates its token and Conversations transactionally.
- Public application options and submissions use the embed token; submissions are normalized, cohort/track-validated, cutoff-checked, and duplicate-protected. Widget CORS is configured with exact deployment origins via `CORS_ALLOWED_ORIGINS`.

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
- Staff onboarding, inactive Profile creation, and a durable email-outbox event are atomic. Email delivery retries independently. Applying this to Talent application approval remains future work.
- Staff setup tokens are single-use and expire after 24 hours. Apply the same setup flow to approved Talents with the application lifecycle.
- Access JWTs expire after 15 minutes; the MVP does not include refresh tokens.
- Admins/Super Admins can create tracks after cohort creation. Staff may list profiles subject to server-enforced permission scoping.
- Bootstrap the first Super Admin through a one-time CLI command that refuses to run if one already exists; do not expose a public bootstrap endpoint.
- Newly onboarded Admin/Mentor Profiles remain inactive until they complete the same one-time password-setup flow as Talents.

## Remaining contract decisions

- Widget hosting location and supported browsers. CORS origin allowlisting is configurable through `CORS_ALLOWED_ORIGINS`.
- Deployment/CI provider, consistent error envelope, and complete list/pagination schemas.
- Detailed per-role filter/result scoping for profile listing.

## Recommended next steps

1. Implement the Talent application approval and rejection workflow, using the existing JWT/role checks and transactional email outbox for one-time Talent setup.
2. Implement messaging and end-to-end lifecycle workflows.
3. Add CI and operational checks, then finalize widget hosting and supported-browser decisions.

See [`04-task-breakdown.md`](./04-task-breakdown.md) for the complete checklist and [`docs/work-plan.md`](../docs/work-plan.md) for the original phase plan.

## Maintenance

Update this file whenever meaningful work is completed. Mark items done only after verification (tests, migration checks, or a reproducible manual check as appropriate). Keep planned requirements separate from verified implementation facts.
