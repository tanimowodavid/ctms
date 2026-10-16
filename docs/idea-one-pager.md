# TMS: Cohort & Talent Management Platform

### Idea One-Pager

- **Track:** Backend Development | Stack: Python, FastAPI, PostgreSQL, Docker
- **Target user:** Accelerator program directors, bootcamp coordinators, and administrators managing multi-track technical cohorts.
- **Problem:** Tech talent programs often rely on fragmented tools to handle applicant intake, track-based mentoring, role permissions, and community communication.
- **Entities:** Cohort, Track, Application, Profile, Conversation, Message
- **Core flow:** Public widget submission creates a cohort-bound application -> Admin reviews and approves the application, creating a Talent profile -> Authenticated messaging in general/track chats
- **In scope:**
  - Role-based access control for users (Super Admin, Admin, Mentor, Talent); applicants are not users until approved
  - Cohort-bound applicant records that admins can review and approve into Talent profiles
  - Cohort-specific public widget script endpoint for applicant intake
  - Normalized messaging system with general cohort and track-specific conversations
  - Global staff management decoupled from single-cohort constraints

- **Out of scope:**
  - Automated peer and AI scoring engines
  - Integrated payment gateway webhooks for fee collection
  - Built-in video conferencing or whiteboard tools
  - Advanced analytics reporting dashboards

- **Top 3 risks:**
  - Enforcing strict role-based permission boundaries across cross-cohort administrative staff.
  - Managing security, validation, and spam control on public-facing widget registration endpoints.
  - Designing scalable relational queries for conversation and message routing across shared tracks.

---

### Weekly update note Week 1:

**Delivered:**

- Idea one-pager and work plan documentation (/docs/idea-one-pager.md)
- Entity Relationship Diagram and database schema definition (/docs/erd.md)
- Comprehensive REST API specification and endpoint design (/docs/api-spec.md)

**Changed after feedback:**

- Non yet

**Key technical decisions:**

- Python with FastAPI chosen for high performance, automatic OpenAPI documentation, and robust async request handling.
- Applications are stored separately from user profiles; approving an application creates a Talent profile, while applicants have no account or role before approval.

**Blockers / risks:**

- Ensuring proper data validation on the public-facing widget intake script to prevent malicious payloads.

**AI and sources used:**

- Gemini AI used to assist in normalizing database relationships, structuring API specifications, and organizing technical markdown documentation.
