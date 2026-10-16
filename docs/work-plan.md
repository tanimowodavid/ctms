# CTMS Work Plan

## Project Goal

Deliver a backend-first cohort and talent management platform with a small application form page and an embeddable JavaScript widget. Staff manage cohorts, tracks, applications, users, and conversations through the API. Talents can use only the chat for their own cohort and assigned track.

## Milestones

### 0. Finalize Product and API Contracts

**Goal:** Make the ERD, API specification, and implementation choices agree before schema and endpoint work begins.

**Work:**

- Confirm lifecycle and permissions for cohorts, tracks, applications, profiles, conversations, and messages.
- Align the ERD with the one-application-per-normalized-email-per-cohort rule, auto-closing intake at `startDate`, automatic role tags, password setup tokens, and unique general/track conversations.
- Decide how one person applying to multiple cohorts interacts with the globally unique profile email and single-cohort talent profile.
- Define staff onboarding credentials and the initial Super Admin bootstrap process.
- Finalize JWT lifetime/refresh behavior, widget script delivery and embedding expectations, and the production email provider when known.
- Add the public widget script and demo/form page delivery contract to the API or implementation documentation.

**Exit criteria:** ERD and API contract describe the same fields, status transitions, permissions, and error cases. Remaining undecided integrations have explicit interfaces and are not blockers for local development.

### 1. Project Foundation, Docker Compose, and CI

**Goal:** Create a reproducible development environment and a fast quality gate.

**Work:**

- Initialize the Python project with `uv`, a pinned Python version, `pyproject.toml`, and committed `uv.lock`.
- Establish the FastAPI application package, configuration loading, environment-variable conventions, and development/test settings.
- Add PostgreSQL and application services to Docker Compose with health checks and persistent local database storage.
- Add test and lint tooling, a minimal health endpoint, and CI to install from the lockfile and run checks on each change.
- Document local setup, test, lint, and migration commands.

**Exit criteria:** A fresh checkout can sync dependencies with `uv`, start the app and PostgreSQL through Compose, pass a health check, and run the same test/lint checks used by CI.

### 2. Database Schema and Migrations

**Goal:** Implement the relational model with database-enforced invariants.

**Work:**

- Create SQLAlchemy 2 models and Alembic configuration/migrations for cohorts, tracks, applications, profiles, conversations, and messages.
- Use database constraints for foreign keys, valid status/role values, unique profile email, unique cohort/email application identity, and one general conversation per cohort and one track conversation per track.
- Normalize application email consistently before persistence and enforce case-insensitive uniqueness in PostgreSQL as well as application validation.
- Ensure a track belongs to the same cohort as its application/profile and that conversation type matches its cohort/track relationship.
- Add migration tests and a repeatable development seed/bootstrap path, including the first Super Admin.

**Exit criteria:** Migrations build a fresh database and upgrade an existing one; tests prove key uniqueness and relationship constraints at the database boundary.

### 3. API Foundation and Shared Behavior

**Goal:** Establish consistent request handling before implementing feature endpoints.

**Work:**

- Add API versioning, request/response schemas, dependency-managed database sessions, and consistent error responses.
- Add structured logging, request validation, pagination conventions, and health/readiness checks.
- Define reusable authorization dependencies and transaction boundaries.
- Generate and review FastAPI OpenAPI output against the API specification.

**Exit criteria:** Shared API behavior is tested, errors are predictable, and the OpenAPI document is available in development.

### 4. Authentication, Profiles, and Staff Permissions

**Goal:** Secure all protected endpoints and implement user lifecycle rules.

**Work:**

- Implement password hashing, login, access-token creation/validation, and inactive/suspended account handling.
- Implement one-time password setup tokens for approved talents; store only a secure token hash, enforce expiry and single use, and activate the profile only after password setup.
- Implement staff onboarding and the Super Admin bootstrap flow; assign role tags automatically.
- Implement staff role changes/revocation and talent suspension/restoration with role-appropriate authorization.
- Test that applicants cannot authenticate and that inactive or suspended users cannot access protected operations.

**Exit criteria:** Authentication and profile lifecycle tests pass for each role and status transition; no endpoint trusts a caller-provided user identity in place of the authenticated profile.

### 5. Cohorts and Tracks

**Goal:** Allow authorized staff to create and manage cohort structures.

**Work:**

- Implement cohort creation with a required, non-empty track list in one database transaction.
- Create the cohort's unique widget token, one general conversation, each track, and each track conversation atomically.
- Implement cohort and track listing with staff-wide visibility and talent visibility limited to their own cohort.
- Implement any post-creation track operations included in the API contract.
- Enforce the intake cutoff using UTC and `now >= startDate`; do not depend on a background job to close applications.

**Exit criteria:** Invalid tracks roll back the entire cohort creation. Tests verify the generated relationships, unique conversations, and role-scoped cohort/track listings.

### 6. Public Application Intake and Widget

**Goal:** Accept valid applications through both the API and the embeddable form.

**Work:**

- Implement the public submission endpoint with strict validation, cohort-token lookup, track/cohort validation, normalized email, and database-backed duplicate prevention.
- Return a conflict for duplicate applications or submissions at/after cohort start; do not store applications rejected by the cutoff.
- Build the standalone widget form page and embeddable JavaScript loader/script, including loading, success, validation, network-error, duplicate, and closed-intake states.
- Document the embedding snippet, required configuration, CORS/origin policy, and supported browser behavior.
- Add abuse controls such as rate limiting and payload-size limits; treat the widget token as public and never as authorization for staff operations.

**Exit criteria:** Browser submission creates exactly one pending application when valid; direct API calls cannot bypass duplicate, track ownership, or cohort-start checks. The widget communicates API results without exposing secrets.

### 7. Application Review and Talent Onboarding

**Goal:** Enable staff to review applications and create talent accounts safely.

**Work:**

- Implement staff-only application list/detail endpoints with cohort and status filters.
- Implement approve and reject actions for Admins and Super Admins; keep pending applications reviewable after intake closes.
- On approval, atomically mark the application approved and create an inactive Talent profile using its cohort and selected track.
- Send a one-time password setup link through the email adapter; activate the talent only after successful setup.
- Handle concurrent/repeated approval safely and test email/profile/application failure boundaries.

**Exit criteria:** An application cannot create more than one profile, approval uses the submitted track, rejection creates no profile, and email delivery failures do not leave inconsistent application/profile state.

### 8. Conversations, Messages, and Authorization

**Goal:** Provide messaging while enforcing the role boundaries on the server.

**Work:**

- Implement accessible conversation discovery, chronological message history, pagination, and message creation.
- Derive sender identity from the authenticated token; never accept `userId` from a message request.
- Allow Super Admins, Admins, and Mentors to read and send in all cohort and track conversations.
- Allow Talents to read and send only in their own cohort's general conversation and assigned track conversation.
- Deny suspended talents conversation discovery, history reads, and sends. Check authorization on every request using the conversation's actual cohort/track relationship, not hidden frontend choices or caller-supplied identifiers.

**Exit criteria:** Tests cover allowed and denied access for every role across cohort general chats, own/other track chats, other cohorts, guessed conversation IDs, and suspended accounts.

### 9. Security, Integration, and Release Readiness

**Goal:** Verify the complete workflows and prepare a dependable initial release.

**Work:**

- Add end-to-end tests for cohort creation, public application, staff review, password setup, login, and messaging.
- Review authentication, authorization, input validation, CORS, rate limiting, secret handling, token expiry, and database transaction behavior.
- Verify migration startup and backup/restore procedures; document environment variables and production email configuration.
- Finalize API and widget integration documentation, runbook, known limitations, and release checklist.

**Exit criteria:** CI passes; a clean Compose environment can migrate and run the complete MVP workflow; security-critical authorization tests pass; deployment and operational requirements are documented.

## Definition of Done

- Every milestone exit criterion passes before work is considered complete.
- Business rules are enforced server-side and, where applicable, by database constraints.
- Automated tests cover success paths, validation failures, authorization failures, and relevant concurrency/duplicate cases.
- The API specification and OpenAPI output reflect implemented behavior.
- Setup, configuration, migrations, tests, and local widget use are documented and reproducible.

## Key Risks and Responses

- **Cross-cohort authorization mistakes:** Centralize policy checks and test both reads and writes, including guessed resource IDs.
- **Public widget abuse:** Apply validation, rate limits, request-size limits, and careful CORS rules; the widget token is public.
- **Duplicate or concurrent applications/approvals:** Normalize email and rely on database uniqueness and transactions, not only pre-check queries.
- **Email provider not selected:** Keep delivery behind an adapter, use a development implementation, and make provider selection a release dependency.
- **Schema/API drift:** Treat the ERD and API contract as versioned implementation references and update them with behavior changes.

## Open Decisions

- Production email provider and sender/domain setup.
- Production hosting/deployment target and CI provider.
- Whether users can apply to multiple cohorts and how an existing Talent profile is handled when another application is approved.
- Staff account password setup and the secure initial Super Admin creation procedure.
- Exact JWT access/refresh token policy and widget hosting/embedding constraints.
