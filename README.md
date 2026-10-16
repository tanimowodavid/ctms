# CTMS

Cohort and Talent management system for organising talents in multiple cohort into their different tracks.

### Project Structure

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
├── alembic/                      # Database Migration History (SQLAlchemy/Alembic)
├── docs/                         # Week 1 Documentation Deliverables
│   ├── idea-one-pager.md         # Problem, target user, core flow, scope, risks
│   ├── work-plan.md              # 3-week execution plan and timeline
│   ├── erd.md                    # Database ERD (Mermaid format)
│   └── api-spec.md               # Comprehensive REST API specifications
│
├── tests/                        # Pytest unit & integration tests
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_applications.py
│
├── .env.example                  # Environment variable template
├── .gitignore                    # Ignored files (venv, __pycache__, .env)
├── pyproject.toml                # Managed via uv (dependencies and metadata)
├── uv.lock                       # uv lock file
└── README.md                     # Project overview, setup instructions, & run guide
```
