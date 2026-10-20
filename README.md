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

```sh
uv run pytest
```

Apply database migrations after configuring `DATABASE_URL` and starting PostgreSQL:

```sh
uv run alembic upgrade head
```

The health endpoint is `GET http://127.0.0.1:8000/health`; it returns:

```json
{ "status": "ok" }
```

## Docker

The project is intended to run using Docker, but Docker configuration and setup are not yet complete. Use the local instructions above for now.

## Project Docs

- [Entity relationship diagram](docs/ERD.md)
- [API specification](docs/api-spec.md)
- [Project overview](docs/idea-one-pager.md)
- [Work plan](docs/work-plan.md)

## Project Structure

```text
CTMS/
├── app/
│   ├── api/                      # Presentation Layer (FastAPI Routers)
│   │   ├── v1/
│   │   │   ├── api.py            # Router aggregator (includes all routers)
│   │   │   └── endpoints/
│   │   │       ├── auth.py         # Login & JWT token management
│   │   │       ├── cohorts.py      # Cohorts, tracks, & widget apply route
│   │   │       ├── profiles.py     # Staff management & applicant approval
│   │   │       └── messages.py     # Normalized conversations & chat messages
│   │   └── deps.py               # FastAPI Dependencies (e.g., get_current_user, get_db)
│   │
│   ├── core/                     # Infrastructure & Configuration
│   │   ├── config.py             # Environment variables (Pydantic Settings)
│   │   ├── database.py           # SQLAlchemy engine & session setup
│   │   └── security.py           # Password hashing (Bcrypt) & JWT utils
│   │
│   ├── models/                   # Database ORM Models (SQLAlchemy Tables)
│   │   ├── cohort.py
│   │   ├── track.py
│   │   ├── application.py        # Dedicated table for public widget leads
│   │   ├── profile.py            # Authenticated users (Admins, Mentors, Talents)
│   │   └── messaging.py          # Conversation & Message models
│   │
│   ├── schemas/                  # Pydantic Validation Schemas (DTOs)
│   │   ├── cohort.py
│   │   ├── application.py
│   │   ├── profile.py
│   │   └── messaging.py
│   │
│   ├── services/                 # Business Logic Layer
│   │   ├── auth_service.py
│   │   ├── profile_service.py
│   │   └── chat_service.py
│   │
│   └── main.py                   # FastAPI app initialization, CORS middleware, routers
│
├── alembic/                      # Alembic configuration and migration history
├── docs/                         # Week 1 Documentation Deliverables
│   ├── idea-one-pager.md         # Problem, target user, core flow, scope, risks
│   ├── work-plan.md              # 3-week execution plan and timeline
│   ├── erd.md                    # Database ERD (Mermaid format)
│   └── api-spec.md               # Comprehensive REST API specifications
│
├── tests/                        # Pytest unit & integration tests
│   ├── conftest.py               # Shared SQLite test database fixtures
│   └── test_model_constraints.py # Database invariant tests
│
├── .env.example                  # Environment variable template
├── .gitignore                    # Ignored files (venv, __pycache__, .env)
├── pyproject.toml                # Managed via uv (dependencies and metadata)
├── uv.lock                       # uv lock file
└── README.md                     # Project overview, setup instructions, & run guide
```
