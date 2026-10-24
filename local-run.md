# Run CTMS and test it with Postman

This guide takes you from a fresh local start to a Talent sending a message. The current workspace already has a demo cohort and accounts. On a fresh local database, you can create the same fixture set with the seed command below.

The seeded accounts are local-only fixtures. They are active so you can sign in right away; the account-creation endpoints below create new accounts as inactive and send password-setup email through the worker.

## 1. Start PostgreSQL and the API

From the repository folder, open PowerShell and run:

```powershell
uv sync
docker compose up -d db
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

Keep the API running in that terminal. It listens on `http://localhost:8000`; its interactive docs are at `http://localhost:8000/docs`. Check that `GET http://localhost:8000/api/v1/health` returns `{"status":"ok"}`.

The local settings live in `.env`. Do not replace an existing `.env` with `.env.example` unless you mean to reset your local configuration. If you are setting up a new checkout, first run `Copy-Item .env.example .env`, then apply migrations as shown above. Compose starts PostgreSQL; the API runs in your terminal.

If your application database is empty and you want the demo cohort and accounts, open another PowerShell terminal and run:

```powershell
uv run python -m app.cli seed-demo
```

Choose and confirm a password of at least 12 characters when prompted. The command creates one future-start cohort, five tracks, and four active demo profiles. It refuses to run if any cohort or profile already exists, so it will not overwrite data. This command is for a disposable local database only. The current workspace was seeded earlier; do not run it again here.

## 2. Sign in with a seeded account

Four demo profiles are active in the local application database:

| Role | Email |
| --- | --- |
| Super Admin | `superadmin@ctms.local` |
| Admin | `admin@ctms.local` |
| Mentor | `mentor1@ctms.local` |
| Mentor | `mentor2@ctms.local` |

The current workspace's four accounts share a local password stored in `.env` under `DEMO_ACCOUNT_PASSWORD`. To print it in your local PowerShell terminal:

```powershell
(Get-Content .env | Where-Object { $_ -like 'DEMO_ACCOUNT_PASSWORD=*' }) -replace '^DEMO_ACCOUNT_PASSWORD=', ''
```

Use the current workspace password only with this local demo database. If you run `seed-demo` on a fresh database, use the password you entered at its prompt instead. Do not reuse either password in another environment or save it in a shared Postman collection. The seeded Super Admin already exists, so the one-time `bootstrap-super-admin` command will correctly refuse to create another one.

These four accounts are fixtures in this workspace's database; they are not automatically added to a fresh database. If you have reset the database, run `uv run python -m app.cli bootstrap-super-admin`, then use the cohort and staff creation requests in this guide. That bootstrap command prompts you for the Super Admin password. New Admin and Mentor profiles start inactive and need the email setup flow below before they can log in.

In Postman, create a collection named **CTMS Local** and add these collection variables:

| Variable | Initial value |
| --- | --- |
| `baseUrl` | `http://localhost:8000/api/v1` |
| `superAdminToken` | *(blank)* |
| `adminToken` | *(blank)* |
| `mentorToken` | *(blank)* |
| `talentToken` | *(blank)* |
| `cohortId` | *(blank)* |
| `embedToken` | *(blank)* |
| `trackId` | *(blank)* |
| `applicationId` | *(blank)* |
| `talentId` | *(blank)* |
| `generalConversationId` | *(blank)* |
| `trackConversationId` | *(blank)* |

Keep tokens and the demo password in Postman's local/current values. Do not share them when exporting a collection.

Add a request named **Login - Super Admin**:

```http
POST {{baseUrl}}/auth/login
Content-Type: application/json
```

```json
{
  "email": "superadmin@ctms.local",
  "password": "<value of DEMO_ACCOUNT_PASSWORD from .env>"
}
```

Expect `200 OK`. In the request's **Scripts → Post-response** tab, save the token:

```javascript
pm.collectionVariables.set("superAdminToken", pm.response.json().accessToken);
```

For protected requests, choose **Authorization → Bearer Token** and enter the matching variable, for example `{{superAdminToken}}`. Access tokens expire after 15 minutes; run Login again when one expires. Repeat the login request with `admin@ctms.local` to save `adminToken`, and with `mentor1@ctms.local` to save `mentorToken`.

## 3. Check the seeded cohort and tracks

Add **List Cohorts**:

```http
GET {{baseUrl}}/cohorts
Authorization: Bearer {{superAdminToken}}
```

The response includes **CTMS Demo Cohort 2027**, its `id`, its public `embedToken`, and five tracks:

1. Backend Engineering
2. Frontend Engineering
3. Data Science and AI
4. Cloud and DevOps
5. Cybersecurity

The cohort accepts applications until `2027-01-11T09:00:00Z`. Copy its `id` and `embedToken` into the collection variables if you want to test this seeded cohort. The guide will create a second cohort next so you can exercise cohort creation without changing the seeded records.

## 4. Create a cohort through the API

Add **Create Cohort**:

```http
POST {{baseUrl}}/cohorts
Authorization: Bearer {{superAdminToken}}
Content-Type: application/json
```

```json
{
  "name": "Postman End-to-End Cohort",
  "startDate": "2030-01-11T09:00:00Z",
  "endDate": "2030-04-11T17:00:00Z",
  "tracks": [
    { "name": "Backend Engineering" },
    { "name": "Frontend Engineering" },
    { "name": "Data Science and AI" },
    { "name": "Cloud and DevOps" },
    { "name": "Cybersecurity" }
  ]
}
```

Expect `201 Created`. The response includes the cohort and track IDs, an `embedToken`, and the generated general and track conversations are available through conversation discovery. Add this post-response script to save the values for the next steps:

```javascript
const cohort = pm.response.json();
pm.collectionVariables.set("cohortId", cohort.id);
pm.collectionVariables.set("embedToken", cohort.embedToken);
pm.collectionVariables.set("trackId", cohort.tracks[0].id);
```

Only Admins and Super Admins can create cohorts. Try the same request with `{{mentorToken}}` and expect `403 Forbidden`.

## 5. Create staff profiles

The seeded Admin and Super Admin are ready for role checks. To test the staff onboarding endpoint, use email addresses you can receive mail at; newly created profiles are inactive until password setup is completed.

As Super Admin, send **Create Admin Profile**:

```http
POST {{baseUrl}}/profiles/staff
Authorization: Bearer {{superAdminToken}}
Content-Type: application/json
```

```json
{
  "fullName": "Postman Test Admin",
  "email": "<an inbox you control>",
  "role": "ADMIN",
  "bio": "Created during the local Postman walkthrough."
}
```

Expect `201 Created` with `status: "INACTIVE"`. An Admin cannot create another Admin; that request returns `403`.

As the seeded Admin, send the same request with a different inbox and `"role": "MENTOR"`. Expect another inactive profile. Admins can create Mentors, while Mentors cannot create staff profiles.

To activate either new profile, configure Gmail SMTP in `.env` with a Google App Password and start the worker in another terminal:

```powershell
docker compose up -d --build email-worker
docker compose logs -f email-worker
```

Open the setup email and copy the `token` query value. This repository does not include a password-setup web page, so finish setup directly in Postman:

```http
POST {{baseUrl}}/auth/setup-password
Content-Type: application/json
```

```json
{
  "setupToken": "<token from the email link>",
  "password": "Choose a password of at least 12 characters"
}
```

Expect `204 No Content`, then log in with the new email and password. Setup links are single-use and expire after 24 hours. If SMTP is not configured, profile creation still succeeds and the email remains queued in the database outbox, but you cannot complete this email-based activation step.

## 6. Test public application intake and the widget

First use Postman to check the public options endpoint. No authorization is needed:

```http
GET {{baseUrl}}/cohorts/{{embedToken}}/application-tracks
```

Expect the cohort name, `acceptingApplications: true`, and five tracks. Now configure the widget origin in `.env`:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:8080
```

Restart the API after changing `.env`, then serve the widget files from a second terminal:

```powershell
python -m http.server 8080 --directory widget
```

Open this URL in your browser, using the `embedToken` saved from the created cohort:

```text
http://localhost:8080/apply.html?apiBase=http://localhost:8000/api/v1&embedToken=YOUR_EMBED_TOKEN
```

The form should show the cohort name and track selector. Submit an applicant using an email inbox you can access, since approval sends the Talent setup email. A successful application shows a confirmation. Submit the same email again to see the duplicate-application message.

You can also test submission directly in Postman with no authorization:

```http
POST {{baseUrl}}/cohorts/{{embedToken}}/apply
Content-Type: application/json
```

```json
{
  "fullName": "Taylor Test Applicant",
  "email": "<a different inbox you control>",
  "trackId": "{{trackId}}"
}
```

Expect `201 Created` with a `PENDING` application. Save the returned `applicationId` as `applicationId`. A repeated email in the same cohort returns `409`; a submission at or after the cohort's UTC `startDate` also returns `409`.

## 7. Review the application and activate the Talent

As the seeded Admin, list pending applications for the test cohort:

```http
GET {{baseUrl}}/applications?cohortId={{cohortId}}&status=PENDING
Authorization: Bearer {{adminToken}}
```

`GET /applications` and application approval/rejection are Admin/Super Admin operations. A Mentor receives `403`.

Approve the application:

```http
POST {{baseUrl}}/applications/{{applicationId}}/approve
Authorization: Bearer {{adminToken}}
```

Expect `201 Created` with a Talent profile in `INACTIVE` status. Save its `id` as `talentId`. The application approval, Talent profile, and email-outbox event are committed together. After the worker delivers the setup email, copy its one-time token and use the `POST /auth/setup-password` request from the previous section. Then log in as the Talent and save the returned token as `talentToken`.

## 8. Send and read messages

As the new Talent, discover the two accessible conversations:

```http
GET {{baseUrl}}/conversations
Authorization: Bearer {{talentToken}}
```

The response contains the cohort's general conversation and the Talent's assigned-track conversation. Copy their `id` values into `generalConversationId` and `trackConversationId`.

Send a message to the track conversation:

```http
POST {{baseUrl}}/conversations/{{trackConversationId}}/messages
Authorization: Bearer {{talentToken}}
Content-Type: application/json
```

```json
{
  "content": "Hello from the Postman end-to-end walkthrough."
}
```

Expect `201 Created`. The API sets `userId` from the login token; a `userId` sent in the body is ignored. Read the chronological history with pagination:

```http
GET {{baseUrl}}/conversations/{{trackConversationId}}/messages?limit=50&offset=0
Authorization: Bearer {{talentToken}}
```

Now list conversations as `{{mentorToken}}`: Staff can discover conversations across cohorts. Try reading or writing to a different cohort's conversation as the Talent; the API returns `404` because that conversation is outside the Talent's access. Try sending a message as the Mentor to confirm staff-wide access.

## 9. Routes available in this checkout

The current application registers these workflows: health, login and password setup, staff creation, cohort and track creation/listing, public application intake, application review, conversation discovery, message history, and message creation. The profile list, staff role-change, staff-revocation, and Talent suspension endpoints described in some planning/API documents are not registered yet; you cannot test them in Postman in this checkout.

For response shapes and constraints, see [the API specification](docs/api-spec.md). For the public form's hosting and embed snippet, see [the widget guide](docs/application-widget.md).
