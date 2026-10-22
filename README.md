# CTMS

CTMS is a cohort and talent management system for organising talents into cohorts and tracks.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLAlchemy with PostgreSQL (`psycopg2`)
- Pydantic Settings
- Alembic, available for database migrations

## Run Locally

Install the project dependencies with `uv`:

```sh
uv sync
```

Start the development server:

```sh
uv run uvicorn app.main:app --reload
```

Run the automated tests:

```powershell
docker compose up -d db
uv run alembic upgrade head
$env:TEST_DATABASE_URL = "postgresql+psycopg2://postgres:change-this-local-password@localhost:5432/ctms_test"
$env:CTMS_MIGRATION_TEST_DATABASE_URL = "postgresql+psycopg2://postgres:change-this-local-password@localhost:5432/ctms_migration_test"
uv run pytest
```

Apply database migrations after configuring `DATABASE_URL` and starting PostgreSQL:

```sh
uv run alembic upgrade head
```

Bootstrap the first Super Admin once, after migration. The command prompts securely for credentials and refuses to create another Super Admin if one already exists:

```sh
uv run python -m app.cli bootstrap-super-admin
```

The PostgreSQL migration integration test runs against a dedicated, empty database. It upgrades to head, checks the schema and revision, then downgrades to base. Compose creates both test databases on first initialization of its persistent PostgreSQL volume.

```powershell
$env:CTMS_MIGRATION_TEST_DATABASE_URL = "postgresql+psycopg2://postgres:change-this-local-password@localhost:5432/ctms_migration_test"
uv run pytest tests/test_migrations.py
```

The health endpoint is `GET http://127.0.0.1:8000/api/v1/health`; it returns:

```json
{ "status": "ok" }
```

## Docker

Start local PostgreSQL with Docker Compose, then apply migrations:

```sh
docker compose up -d db
uv run alembic upgrade head
```

Compose publishes PostgreSQL on port 5432, stores its data in the `postgres_data` volume, and waits for `pg_isready` before reporting the database healthy. It creates `ctms_test` and `ctms_migration_test` on initial database setup. Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_PORT` in `.env` to override local defaults. Build the API image separately with `docker build -t ctms .`.

## Staff onboarding and email worker

Copy `.env.example` to `.env` and replace the JWT secret and Gmail SMTP placeholders. For Gmail, create an App Password and use it as `SMTP_PASSWORD`; do not use your regular Gmail password. `DATABASE_URL` is for the API running on the host; `WORKER_DATABASE_URL` uses the Compose database host name. Run migrations before starting the worker:

```sh
uv run alembic upgrade head
docker compose up -d --build email-worker
```

The staff endpoint is `POST /api/v1/profiles/staff`. An Admin may create Mentors; a Super Admin may create Admins. Each new Profile is inactive, and its profile plus a durable outbox event are committed together. The separate worker sends the setup email and retries failed delivery with exponential backoff, capped by `WORKER_RETRY_MAX_SECONDS`. Setup tokens are stored as hashes and expire after 24 hours. Configure `SETUP_LINK_BASE_URL` to the page that accepts the `token` query parameter and posts the chosen password to `POST /api/v1/auth/setup-password`.

`POST /api/v1/auth/login` returns a 15-minute JWT for active users. Protected requests use `Authorization: Bearer <accessToken>`.

## Project Docs

- [Entity relationship diagram](docs/ERD.md)
- [API specification](docs/api-spec.md)
- [Project overview](docs/idea-one-pager.md)
- [Work plan](docs/work-plan.md)

## Project Structure

```text
CTMS/
├── app/
│   ├── api/                      # HTTP routers and request dependencies
│   ├── core/                     # Configuration, database, and security
│   ├── models/                   # SQLAlchemy persistence models
│   ├── schemas/                  # Request and response validation
│   ├── services/                 # Business workflows
│   ├── cli.py                    # Operator commands such as first-admin setup
│   └── main.py                   # FastAPI application
├── alembic/                      # Database migration history
├── docs/                         # Product and API references
├── tests/                        # Automated tests
├── docker-compose.yml            # Local PostgreSQL service
├── Dockerfile                    # API image
├── pyproject.toml                # Dependencies and project configuration
└── README.md
```
