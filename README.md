# CTMS

CTMS helps a training program manage cohorts, tracks, applications, and participant conversations. Staff create cohorts and review applications; approved Talents set up their accounts and can chat in their cohort’s general conversation and assigned track conversation.

The project is a FastAPI backend with a small public application form that can be hosted separately and embedded on another site.

## Project notes

- [Local run and Postman end-to-end guide](local-run.md)
- [API specification](docs/api-spec.md)
- [Data model](docs/ERD.md)
- [Application widget setup](docs/application-widget.md)
- [Project overview](docs/idea-one-pager.md)
- [Work plan](docs/work-plan.md)

The code is organized by responsibility: HTTP routes live in `app/api`, validation schemas in `app/schemas`, business workflows in `app/services`, and database models in `app/models`.

## What’s included

- Staff login, onboarding, and one-time password setup links.
- Cohort and track management, with a public application widget.
- Admin and Super Admin application review and Talent onboarding.
- Conversation discovery, message history, and messaging permissions for Staff and Talents.
- PostgreSQL persistence, Alembic migrations, and an email outbox worker.

## Run it locally

You’ll need Python 3.12+, [`uv`](https://docs.astral.sh/uv/), and Docker Compose. From the repository root, create your local environment, install dependencies, start PostgreSQL, and apply the schema:

```powershell
Copy-Item .env.example .env
uv sync
docker compose up -d db
uv run alembic upgrade head
```

The example settings are for local development. Keep `.env` private and replace the JWT secret before using the API beyond local work. Start the API with:

```powershell
uv run uvicorn app.main:app --reload
```

The API listens at `http://localhost:8000`. Interactive documentation is at `http://localhost:8000/docs`, and the health check is `GET /api/v1/health`.

The first account must be a Super Admin. Create it once, after applying migrations:

```powershell
uv run python -m app.cli bootstrap-super-admin
```

The command prompts for credentials and refuses to create a second Super Admin. Admins and Super Admins can create cohorts and review applications. Mentors and newly approved Talents complete account setup through a one-time email link.

For a disposable local database, you can create a complete Postman demo dataset instead of bootstrapping an individual Super Admin:

```powershell
uv run python -m app.cli seed-demo
```

The command prompts for one password and creates a future-start cohort, five tracks, and active Super Admin, Admin, and Mentor demo accounts. All four accounts share the password you enter. It refuses to run if the database already contains a profile or cohort, and it does not delete or overwrite existing data. Use this only for local development; the seeded accounts use reserved `.local` email addresses and are not intended for real email delivery. See [the Postman walkthrough](learn.md) for the account names and end-to-end steps.

## Try the application form

The widget needs a cohort with at least one track and a future `startDate`. In `/docs`, log in through `POST /api/v1/auth/login`, select **Authorize**, and create a cohort through `POST /api/v1/cohorts`. Copy its `embedToken`.

Allow the local widget origin in `.env` and restart the API so it picks up the setting:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:8080
```

Serve the widget directory in another terminal:

```powershell
python -m http.server 8080 --directory widget
```

Open the form with your cohort token:

```text
http://localhost:8080/apply.html?apiBase=http://localhost:8000/api/v1&embedToken=YOUR_COHORT_TOKEN
```

Applicants do not need an account. The widget token is public intake configuration, not an access credential. For a hosted site, configure the exact widget origin in `CORS_ALLOWED_ORIGINS` and follow the [widget setup guide](docs/application-widget.md) for the embed snippet.

## Run the tests

`.env.example` includes separate PostgreSQL URLs for the application tests and the fresh migration test. Keep both pointed at disposable databases whose names end in `_test`; Compose creates them when it first initializes its database volume.

```powershell
uv run pytest -q
```

The migration test expects its own empty database and upgrades it to the latest revision before cleaning it up. Do not point either test URL at a database containing data you need.

## Email delivery

Email runs in a separate Compose worker. To test setup links locally, configure Gmail SMTP in `.env` with a Google App Password (not your regular account password), then start the worker:

```powershell
docker compose up -d --build email-worker
```

The API stores email work in PostgreSQL’s outbox; the worker sends it and retries failures. `DATABASE_URL` is used by the API on your host, while `WORKER_DATABASE_URL` uses the Compose service name `db`. Set `SETUP_LINK_BASE_URL` to the page that reads the `token` query parameter and submits the chosen password to `POST /api/v1/auth/setup-password`.

## PostgreSQL and Docker

Compose runs PostgreSQL 16 on port 5432 and stores its data in the `postgres_data` volume. It also creates `ctms_test` and `ctms_migration_test` on the first initialization. Set `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, or `POSTGRES_PORT` in `.env` to change the local defaults.

PostgreSQL reads `POSTGRES_PASSWORD` when it initializes a new data volume. Changing that setting later does not change the password already stored in an existing volume; update the PostgreSQL role password as well if you rotate it.

The Dockerfile builds the API image, but Compose currently starts only PostgreSQL and the email worker. Build the API image with `docker build -t ctms .`.
