# TMS: Cohort & Talent Management Platform

### Idea One-Pager

- **Track:** Backend Development | Stack: Python, FastAPI, PostgreSQL, Docker
- **Target user:** Accelerator program directors, bootcamp coordinators, and administrators managing multi-track technical cohorts.
- **Problem:** Tech talent programs often rely on fragmented tools to handle applicant intake, track-based mentoring, role permissions, and community communication.
- **Entities:** Cohort, Track, Profile, Conversation, Message
- **Core flow:** Public widget submission (POST /api/cohorts/{embedToken}/apply) -> Admin review & talent promotion (PATCH /api/profiles/{id}) -> Authenticated messaging in general/track chats (POST /api/conversations/{id}/messages)
- **In scope:**
  - Role-based access control (Super Admin, Admin, Mentor, Talent, Applicant)
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
- Single Profile table architecture with Enum roles implemented to cleanly handle transitions from Applicant to Talent while maintaining unified user data.

**Blockers / risks:**

- Ensuring proper data validation on the public-facing widget intake script to prevent malicious payloads.

**AI and sources used:**

- Gemini AI used to assist in normalizing database relationships, structuring API specifications, and organizing technical markdown documentation.
