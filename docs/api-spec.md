# TMS API Specification

This document outlines the RESTful API endpoints for the **TMS** platform, built using Python and FastAPI. The architecture supports public applicant intake via embedded widgets, role-based user management (Super Admin, Admin, Mentor, Talent), and normalized chat messaging. Applicants are cohort-bound application records, not users; an approved application creates a Talent profile.

---

## Base URL

```text
https://api.tms.internal/api/v1
```

---

## Authentication & Authorization Headers

Protected endpoints require a Bearer token in the authorization header:

```http
Authorization: Bearer <jwt_access_token>
```

Super Admins, Admins, and Mentors are staff and can access conversations across all cohorts and tracks. Talents can access only the general conversation for their own cohort and the track conversation for their assigned track. The API enforces these rules on conversation discovery, message history, and message creation; frontend filtering is not an authorization boundary. Suspended talents cannot access conversations or messages.

---

## 1. Public Widget Endpoints (Unauthenticated)

### Submit Cohort Application

- **Method:** `POST`
- **Path:** `/cohorts/{embedToken}/apply`
- **Description:** Allows prospective students to apply directly to a specific cohort using the public JavaScript widget token.
- **Rules:** The token is valid only before the cohort's `startDate` (UTC). At or after that time, the cohort has started and submissions are rejected without creating an application. Email addresses are trimmed and compared case-insensitively; only one application per email is allowed in each cohort, regardless of selected track.
- **Request Body:**
  ```json
  {
    "fullName": "Jane Doe",
    "email": "jane.doe@example.com",
    "trackId": "d3b07384-d113-4ec6-a579-24d1a58c0c45"
  }
  ```
- **Responses:**
  - `201 Created`: Application received successfully.
    ```json
    {
      "message": "Application submitted successfully",
      "applicationId": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "status": "PENDING"
    }
    ```
  - `400 Bad Request`: Invalid request or a track that does not belong to the cohort.
  - `404 Not Found`: Invalid cohort embed token.
  - `409 Conflict`: An application already exists for this email in the cohort, or the cohort has started and intake is closed.

---

## 2. Authentication Endpoints

### User Login

- **Method:** `POST`
- **Path:** `/auth/login`
- **Description:** Authenticates active users (Staff, Mentors, Talents) and returns a JWT access token.
- **Request Body:**
  ```json
  {
    "email": "admin@talentflow.internal",
    "password": "SecurePassword123!"
  }
  ```
- **Responses:**
  - `200 OK`: Authentication successful.
    ```json
    {
      "accessToken": "eyJhbGciOiJIUzI1Ni...",
      "tokenType": "bearer",
      "user": {
        "id": "e7b07384-d113-4ec6-a579-24d1a58c0c11",
        "email": "admin@talentflow.internal",
        "fullName": "System Administrator",
        "role": "ADMIN"
      }
    }
    ```
  - `401 Unauthorized`: Invalid credentials.

### Complete Talent Password Setup

- **Method:** `POST`
- **Path:** `/auth/setup-password`
- **Description:** Completes account setup using the one-time token emailed after application approval. On success, stores the password hash and changes the Talent profile from `INACTIVE` to `ACTIVE`.
- **Request Body:**
  ```json
  {
    "setupToken": "one-time-token",
    "password": "ChooseAStrongPassword123!"
  }
  ```
- **Responses:**
  - `204 No Content`: Password set and account activated.
  - `400 Bad Request`: Invalid or expired token, or password does not meet requirements.

---

## 3. Cohorts & Tracks Management

### Create Cohort (Super Admin / Admin)

- **Method:** `POST`
- **Path:** `/cohorts`
- **Description:** Creates a new training cohort, its unique widget `embedToken`, its default general conversation, and one or more tracks. A non-empty track list is required. The cohort and all tracks are created atomically; if any track is invalid, nothing is created. Cohort intake closes automatically at `startDate` (UTC); pending applications remain reviewable after that time.
- **Request Body:**
  ```json
  {
    "name": "Cohort 1 - Fall 2026",
    "startDate": "2026-11-01T00:00:00Z",
    "endDate": "2027-02-01T00:00:00Z",
    "tracks": [
      { "name": "Backend Development" },
      { "name": "Frontend Development" }
    ]
  }
  ```
- **Responses:**
  - `201 Created`: Cohort created successfully.
    ```json
    {
      "id": "cohort-uuid",
      "name": "Cohort 1 - Fall 2026",
      "embedToken": "cohort-widget-token",
      "tracks": [
        { "id": "track-uuid-1", "name": "Backend Development" },
        { "id": "track-uuid-2", "name": "Frontend Development" }
      ]
    }
    ```
  - `400 Bad Request`: Invalid cohort or track data.

### List Cohorts

- **Method:** `GET`
- **Path:** `/cohorts`
- **Description:** Staff can retrieve all cohorts. Talents can retrieve only their own cohort; the server scopes results using the authenticated user's profile, not client-supplied filters.
- **Responses:**
  - `200 OK`: Returns an array of cohort objects.

### Create Track

- **Method:** `POST`
- **Path:** `/cohorts/{cohortId}/tracks`
- **Description:** Adds a specialized learning track (e.g., Backend, Frontend) to a cohort and creates its track-specific conversation thread. This is for adding tracks after cohort creation; initial tracks are created with the cohort.
- **Request Body:**
  ```json
  {
    "name": "Backend Development"
  }
  ```
- **Responses:**
  - `201 Created`: Track created successfully.

### List Tracks in a Cohort

- **Method:** `GET`
- **Path:** `/cohorts/{cohortId}/tracks`
- **Description:** Lists tracks in a cohort. Staff can access tracks across cohorts; talents can access only tracks in their own cohort. Talents may send messages only in their assigned track's conversation.
- **Responses:**
  - `200 OK`: Returns the authorized tracks.
  - `403 Forbidden`: The authenticated user is not authorized for this cohort.
  - `404 Not Found`: Cohort not found.

---

## 4. User & Profile Management

### List Profiles (Filtered by Role/Cohort)

- **Method:** `GET`
- **Path:** `/profiles`
- **Query Parameters:** `role` (optional), `cohortId` (optional), `trackId` (optional)
- **Description:** Allows staff and mentors to filter profiles based on permissions.
- **Responses:**
  - `200 OK`: Returns a filtered list of user profiles.

### List Applications (Admin / Super Admin)

- **Method:** `GET`
- **Path:** `/applications`
- **Query Parameters:** `cohortId` (optional), `status` (optional, e.g. `PENDING`, `APPROVED`, `REJECTED`)
- **Description:** Lists application records for staff review. Applicants are not profiles and cannot authenticate. Intake closure does not prevent staff from reviewing pending applications.
- **Responses:**
  - `200 OK`: Returns matching applications.
  - `403 Forbidden`: The user is not an Admin or Super Admin.

### Get Application (Admin / Super Admin)

- **Method:** `GET`
- **Path:** `/applications/{applicationId}`
- **Description:** Retrieves one application for staff review.
- **Responses:**
  - `200 OK`: Returns the application.
  - `403 Forbidden`: The user is not an Admin or Super Admin.
  - `404 Not Found`: Application not found.

### Approve Application (Admin / Super Admin)

- **Method:** `POST`
- **Path:** `/applications/{applicationId}/approve`
- **Description:** Approves a pending application and atomically creates an `INACTIVE` Talent profile using the applicant's name, email, cohort, and selected track. The applicant receives a one-time email setup link to create their password; completing setup stores the password hash and activates the profile. Approval is allowed after cohort intake closes. Repeated approval of an already processed application is rejected.
- **Request Body:**
  No request body. The application’s selected track is used.
- **Responses:**
  - `201 Created`: Application approved and Talent profile created.
  - `403 Forbidden`: The user is not an Admin or Super Admin.
  - `404 Not Found`: Application not found.
  - `409 Conflict`: Application is not pending, or a profile already exists for the email.

### Reject Application (Admin / Super Admin)

- **Method:** `POST`
- **Path:** `/applications/{applicationId}/reject`
- **Description:** Marks a pending application as `REJECTED`. This does not create a user profile. Repeated rejection or rejection of an already processed application is rejected.
- **Responses:**
  - `200 OK`: Application rejected.
  - `403 Forbidden`: The user is not an Admin or Super Admin.
  - `404 Not Found`: Application not found.
  - `409 Conflict`: Application is not pending.

### Onboard Staff / Mentor

- **Method:** `POST`
- **Path:** `/profiles/staff`
- **Description:** Provisions a new admin or mentor account. Admins can create mentors; Super Admins can create admins.
- **Request Body:**
  ```json
  {
    "fullName": "Dr. Smith",
    "email": "smith@talentflow.internal",
    "role": "MENTOR",
    "bio": "Expert system architect and engineering lead."
  }
  ```
- **Responses:**
  - `201 Created`: Staff member created.
  - The profile tag is assigned automatically from the role and is not supplied by the caller.

### Change Staff Role or Revoke Staff Access (Super Admin)

- **Method:** `PATCH`
- **Path:** `/profiles/{profileId}/staff-access`
- **Description:** Allows a Super Admin to change an existing Admin's role to Mentor or an existing Mentor's role to Admin. Setting status to `INACTIVE` revokes staff access. Role tags are updated automatically. This endpoint cannot create or modify Super Admin accounts.
- **Request Body:** Provide one or both fields.
  ```json
  {
    "role": "MENTOR",
    "status": "ACTIVE"
  }
  ```
- **Responses:**
  - `200 OK`: Staff access updated.
  - `400 Bad Request`: Unsupported role or status.
  - `403 Forbidden`: The user is not a Super Admin.
  - `404 Not Found`: Staff profile not found.

### Suspend or Restore Talent (Admin / Super Admin)

- **Method:** `PATCH`
- **Path:** `/profiles/{profileId}/status`
- **Description:** Sets a Talent profile's status to `SUSPENDED` or restores it to `ACTIVE`. Suspended talents cannot discover conversations, read message history, or send messages. Only Admins and Super Admins can change a Talent's status.
- **Request Body:**
  ```json
  {
    "status": "SUSPENDED"
  }
  ```
- **Responses:**
  - `200 OK`: Profile status updated.
  - `400 Bad Request`: Unsupported status value.
  - `403 Forbidden`: The user is not an Admin or Super Admin.
  - `404 Not Found`: Talent profile not found.

---

## 5. Normalized Messaging Endpoints

### List Accessible Conversations

- **Method:** `GET`
- **Path:** `/conversations`
- **Description:** Returns only conversations the authenticated user may access. Staff (Super Admin, Admin, Mentor) receive conversations across all cohorts and tracks. Talents receive only their own cohort's general conversation and their assigned track's conversation. Suspended talents are denied access. Authorization is derived from the authenticated profile; clients cannot gain access by supplying another cohort, track, or conversation ID.
- **Responses:**
  - `200 OK`: Returns the authorized conversations.
  - `403 Forbidden`: The user is suspended or otherwise not authorized.

### List Messages in a Conversation

- **Method:** `GET`
- **Path:** `/conversations/{conversationId}/messages`
- **Query Parameters:** `limit` (default 50), `offset` (default 0)
- **Description:** Retrieves historical messages for either a general cohort conversation or a track conversation.
- **Authorization:** Staff can read all conversations. Talents can read only their own cohort's general conversation and assigned track conversation. Suspended talents are denied access.
- **Responses:**
  - `200 OK`: Returns chronological array of messages with sender data.

### Send Message

- **Method:** `POST`
- **Path:** `/conversations/{conversationId}/messages`
- **Description:** Posts a new message into a conversation thread.
- **Authorization:** Staff can send messages in all conversations. Talents can send only in their own cohort's general conversation and assigned track conversation. The sender `userId` is taken from the access token, never from the request body. Suspended talents are denied access.
- **Request Body:**
  ```json
  {
    "content": "Hello team, welcome to the first assignment kickoff!"
  }
  ```
- **Responses:**
  - `201 Created`: Message sent successfully.
    ```json
    {
      "id": "c8b07384-d113-4ec6-a579-24d1a58c0c99",
      "conversationId": "uuid-string",
      "userId": "uuid-string",
      "content": "Hello team, welcome to the first assignment kickoff!",
      "createdAt": "2026-10-13T12:30:00Z"
    }
    ```
