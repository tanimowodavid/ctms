# CTMS Agent Task Breakdown

Use this as the implementation checklist. Items describe intended product work; completion must be reflected in [`progress-tracker.md`](./progress-tracker.md) and verified with tests. Resolve open product/API decisions before making incompatible assumptions.

## 0. Contract and decisions

- [x] Reconcile the ERD, API contract, product spec, and actual implementation; record model gaps in the progress tracker before migrations.
- [x] Decide Talent cohort assignment: one cohort/track assignment at a time; an existing Profile email cannot be approved a second time; multi-cohort enrollment is outside the MVP.
- [x] Specify initial Super Admin bootstrap (one-time CLI only when none exists) and Staff password setup (inactive until one-time setup-link completion).
- [x] Specify MVP JWT policy: 15-minute access tokens, no refresh-token flow.
- [x] Specify setup-token policy: single-use, 24-hour expiry.
- [x] Specify email failure policy: persist approval/Profile/outbox atomically and retry delivery independently.
- [ ] Specify widget hosting, embed snippet, allowed origins/CORS, and browser support.
- [ ] Specify consistent error response format and list response schemas/pagination limits.
- [x] Clarify post-creation track creation (Admin/Super Admin), profile listing (Staff with server-enforced scoping), and cohort creation (Admin/Super Admin).

## 1. Project foundation and quality gates

- [x] Complete Dockerfile and Docker Compose with PostgreSQL health checks and persistent local database storage.
- [ ] Add CI to install from the `uv` lockfile and run tests and quality checks.
- [ ] Select and configure formatter/linter/type-checking tools; document exact commands.
- [ ] Document database, environment, migration, test, and development workflows.
- [ ] Add health and readiness behavior suitable for local and deployed use.
- [ ] Verify clean-checkout setup and application startup.

## 2. Data layer and migrations

- [x] Review SQLAlchemy models against the ERD and API contract.
- [x] Configure Alembic and create the initial migration.
- [x] Add foreign keys and uniqueness for Profile email, cohort/embed token, case/space-insensitive cohort/Application email, and unique general/track Conversations.
- [x] Ensure every Application/Profile Track belongs to its Cohort through composite foreign keys.
- [x] Enforce valid role, status, and Conversation type/relationship invariants.
- [ ] Normalize email at the application intake boundary before persistence; the database already rejects case/space-insensitive duplicates.
- [x] Add a PostgreSQL migration test, one-time Super Admin bootstrap CLI, and verify the initial migration on a fresh local PostgreSQL database.

## 3. API foundation

- [x] Wire API v1 routers into the FastAPI application.
- [ ] Define request and response Pydantic schemas for every endpoint.
- [ ] Implement database session lifecycle and consistent exception/error responses.
- [ ] Add reusable current-user and role/resource authorization dependencies.
- [ ] Add structured logging that excludes passwords, tokens, and other secrets.
- [ ] Define pagination validation and list response conventions.
- [ ] Compare generated OpenAPI output with the API contract.

## 4. Authentication and profile lifecycle

- [ ] Implement password hashing and verification using the selected safe configuration.
- [ ] Implement login and signed access-token creation/validation.
- [ ] Reject inactive accounts from login and apply status checks to protected requests.
- [ ] Implement secure, one-time Talent setup tokens and password setup activation.
- [ ] Enforce 24-hour setup-token expiry and single-use consumption.
- [ ] Implement the durable email outbox and retryable setup-link delivery without rolling back approval on provider failure.
- [ ] Enforce 15-minute access JWT expiry; do not add a refresh flow in the MVP.
- [ ] Implement staff onboarding with role restrictions and automatic role tags.
- [ ] Implement Super Admin-only Admin/Mentor role changes and staff revocation.
- [ ] Implement Admin/Super Admin Talent suspension and restoration.
- [x] Implement documented Super Admin bootstrap mechanism.
- [ ] Test applicant, inactive, active, and suspended authentication/authorization behavior.

## 5. Cohorts and tracks

- [ ] Implement atomic cohort creation with at least one valid track.
- [ ] Generate unique public embed token.
- [ ] Create one general Conversation per Cohort and one track Conversation per Track.
- [ ] Implement role-scoped cohort and track listing.
- [ ] Implement post-creation track creation and its Conversation.
- [ ] Apply UTC cohort-start intake boundary consistently (`now >= startDate` is closed).
- [ ] Test transactional rollback, track ownership, unique conversations, and role scoping.

## 6. Public application intake and widget

- [ ] Implement widget-token lookup and public submission endpoint.
- [ ] Validate full name, email, and track; normalize email.
- [ ] Enforce track/cohort relationship, case-insensitive cohort duplicate prevention, and start-time cutoff.
- [ ] Handle concurrent duplicate submissions with database constraints and a conflict response.
- [ ] Build the standalone application form and embeddable JavaScript loader.
- [ ] Implement loading, success, validation, duplicate, closed-intake, and network-error states.
- [ ] Configure safe CORS/origin behavior, request size limits, and rate limiting.
- [ ] Document widget installation and public-token limitations.

## 7. Application review and Talent onboarding

- [ ] Implement staff-only Application list/detail and filters.
- [ ] Implement Admin/Super Admin approval and rejection state transitions.
- [ ] Atomically create one inactive Talent Profile and approve its Application.
- [ ] Prevent repeated/concurrent approvals and handle globally duplicated Profile email.
- [ ] Add an email adapter and development implementation for setup links.
- [ ] Implement single-use password setup and activation.
- [ ] Test post-intake review, rejection, duplicates, concurrent approval, and email failures.

## 8. Messaging and authorization

- [ ] Implement accessible Conversation discovery.
- [ ] Implement chronological Message history with validated pagination and sender data.
- [ ] Implement message creation with sender identity derived only from authentication.
- [ ] Allow staff access across cohorts/tracks.
- [ ] Allow Talents access only to own cohort general chat and assigned track chat.
- [ ] Deny suspended Talent access to discovery, reads, and writes.
- [ ] Test guessed IDs, other cohorts/tracks, unauthorized roles, and all allowed paths.

## 9. Integration and release

- [ ] Add end-to-end happy-path tests: cohort → application → review → setup → login → messaging.
- [ ] Review authentication, authorization, validation, CORS, rate limits, secrets, token lifecycle, and transaction behavior.
- [ ] Verify migrations and restore/backup approach.
- [ ] Complete deployment configuration and operations documentation.
- [ ] Run full CI checks and verify clean Docker Compose startup.
- [ ] Update source docs and this planning set whenever behavior changes.
