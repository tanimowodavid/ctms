# CTMS Agent Task Breakdown

Use this as the implementation checklist. Items describe intended product work; completion must be reflected in [`progress-tracker.md`](./progress-tracker.md) and verified with tests. Resolve open product/API decisions before making incompatible assumptions.

## 0. Contract and decisions

- [x] Reconcile the ERD, API contract, product spec, and actual implementation; record model gaps in the progress tracker before migrations.
- [x] Decide Talent cohort assignment: one cohort/track assignment at a time; an existing Profile email cannot be approved a second time; multi-cohort enrollment is outside the MVP.
- [x] Specify initial Super Admin bootstrap (one-time CLI only when none exists) and Staff password setup (inactive until one-time setup-link completion).
- [x] Specify MVP JWT policy: 15-minute access tokens, no refresh-token flow.
- [x] Specify setup-token policy: single-use, 24-hour expiry.
- [x] Specify email failure policy: persist approval/Profile/outbox atomically and retry delivery independently.
- [ ] Specify widget hosting and browser support. CORS uses the configured exact-origin allowlist.
- [ ] Specify consistent error response format and list response schemas/pagination limits.
- [x] Clarify post-creation track creation (Admin/Super Admin), profile listing (Staff with server-enforced scoping), and cohort creation (Admin/Super Admin).

## 1. Project foundation and quality gates

- [x] Complete Dockerfile and Docker Compose with PostgreSQL health checks and persistent local database storage.
- [ ] Add CI to install from the `uv` lockfile and run tests and quality checks.
- [ ] Select and configure formatter/linter/type-checking tools; document exact commands.
- [x] Document database, environment, migration, PostgreSQL test, and development workflows.
- [ ] Add health and readiness behavior suitable for local and deployed use.
- [ ] Verify clean-checkout setup and application startup.

## 2. Data layer and migrations

- [x] Review SQLAlchemy models against the ERD and API contract.
- [x] Configure Alembic and create the initial migration.
- [x] Add foreign keys and uniqueness for Profile email, cohort/embed token, case/space-insensitive cohort/Application email, and unique general/track Conversations.
- [x] Ensure every Application/Profile Track belongs to its Cohort through composite foreign keys.
- [x] Enforce valid role, status, and Conversation type/relationship invariants.
- [x] Normalize email at the application intake boundary before persistence; the database rejects case/space-insensitive duplicates.
- [x] Add a PostgreSQL migration test, one-time Super Admin bootstrap CLI, and verify the initial migration on a fresh local PostgreSQL database.

## 3. API foundation

- [x] Wire API v1 routers into the FastAPI application.
- [ ] Define request and response Pydantic schemas for every endpoint.
- [x] Implement database session lifecycle and current-user/role authorization dependencies for the delivered auth and staff onboarding routes. Consistent exception/error responses remain pending.
- [ ] Add structured logging that excludes passwords, tokens, and other secrets.
- [ ] Define pagination validation and list response conventions.
- [ ] Compare generated OpenAPI output with the API contract.

## 4. Authentication and profile lifecycle

- [x] Implement password hashing and verification using the selected safe configuration.
- [x] Implement login and signed access-token creation/validation.
- [x] Reject inactive accounts from login and apply status checks to protected requests.
- [x] Implement secure, one-time staff setup tokens and password setup activation.
- [x] Enforce 24-hour setup-token expiry and single-use consumption for staff setup.
- [x] Integrate the durable email outbox with Talent application approval. Staff onboarding uses the outbox and retryable setup-link delivery.
- [x] Enforce 15-minute access JWT expiry; do not add a refresh flow in the MVP.
- [x] Implement staff onboarding with role restrictions and automatic role tags.
- [ ] Implement Super Admin-only Admin/Mentor role changes and staff revocation.
- [ ] Implement Admin/Super Admin Talent suspension and restoration.
- [x] Implement documented Super Admin bootstrap mechanism.
- [ ] Test applicant and suspended Talent authentication/authorization behavior. Active/inactive staff login and role authorization are covered.

## 5. Cohorts and tracks

- [x] Implement atomic cohort creation with at least one valid track.
- [x] Generate unique public embed token.
- [x] Create one general Conversation per Cohort and one track Conversation per Track.
- [x] Implement role-scoped cohort and track listing.
- [x] Implement post-creation track creation and its Conversation.
- [x] Apply UTC cohort-start intake boundary consistently (`now >= startDate` is closed).
- [x] Test transactional rollback, track ownership, unique conversations, and role scoping.

## 6. Public application intake and widget

- [x] Implement widget-token lookup and public submission endpoint.
- [x] Validate full name, email, and track; normalize email.
- [x] Enforce track/cohort relationship, case-insensitive cohort duplicate prevention, and start-time cutoff.
- [x] Handle concurrent duplicate submissions with database constraints and a conflict response.
- [x] Build the standalone application form and embeddable JavaScript loader.
- [x] Implement loading, success, validation, duplicate, closed-intake, and network-error states.
- [x] Configure CORS with an exact origin allowlist; request-size limits remain unconfigured.
- [x] Document widget installation and public-token limitations.

Rate limiting and bot protection are out of scope for this project.

## 7. Application review and Talent onboarding

- [x] Implement staff-only Application list/detail and filters.
- [x] Implement Admin/Super Admin approval and rejection state transitions.
- [x] Atomically create one inactive Talent Profile and approve its Application.
- [x] Prevent repeated/concurrent approvals and handle globally duplicated Profile email.
- [x] Reuse the SMTP outbox worker for Talent setup links, with a Talent-specific email message.
- [x] Reuse single-use password setup and activation for approved Talents.
- [x] Test post-intake review, rejection, duplicate-profile conflict, and retryable outbox delivery.

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
