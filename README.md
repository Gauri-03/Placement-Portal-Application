# LaunchPad — Placement Portal Application V2

> A full-stack campus recruitment management system for institutes, companies, and students.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Three-Role System & Business Logic](#3-three-role-system--business-logic)
   - [Admin](#31-admin--institute-placement-cell)
   - [Company](#32-company)
   - [Student](#33-student)
4. [Core Business Rules](#4-core-business-rules)
5. [Data Models](#5-data-models)
6. [Status Lifecycles](#6-status-lifecycles)
7. [Tech Stack](#7-tech-stack)
8. [Prerequisites](#8-prerequisites)
9. [Setup & Running](#9-setup--running)
10. [Default Credentials](#10-default-credentials)
11. [Background Jobs (Celery)](#11-background-jobs-celery)
12. [Frontend Routes](#12-frontend-routes)
13. [API Overview](#13-api-overview)
14. [Seed Data](#14-seed-data)
15. [Environment Variables](#15-environment-variables)
16. [Project Structure](#16-project-structure)

---

## 1. Project Overview

**LaunchPad** is a centralized campus placement portal that replaces manual spreadsheet/email-based recruitment coordination. It connects three types of users on a single platform:

| Role        | Who                      | What they do                                           |
| ----------- | ------------------------ | ------------------------------------------------------ |
| **Admin**   | Institute Placement Cell | Approves companies & drives, oversees all activity     |
| **Company** | Recruiting organizations | Creates placement drives, manages student applications |
| **Student** | Job-seeking students     | Applies to drives, tracks application status           |

### Problems Solved

| Problem                                 | Solution                                                       |
| --------------------------------------- | -------------------------------------------------------------- |
| Manual company approval via email       | Admin dashboard with one-click approve/reject                  |
| Students missing application deadlines  | Automated daily email reminders (Celery Beat)                  |
| No visibility into placement statistics | Admin monthly report + dashboard stats                         |
| Duplicate applications                  | Database-level unique constraint + server-side check           |
| Ineligible students applying            | Eligibility validation (branch, CGPA, year) before application |
| No centralized placement history        | Complete application history per student with CSV export       |
| Manual CSV exports                      | Async Celery job — CSV emailed to student automatically        |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT (Browser)                      │
│              Vue 3 SPA  ·  Vue Router (hash mode)        │
│              Bootstrap 5.3.8 CDN  ·  Native fetch API    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/JSON  +  JWT Bearer Token
                       │ http://localhost:5000
                       │
┌──────────────────────▼──────────────────────────────────┐
│                  FLASK REST API  (port 5000)              │
│                                                          │
│  /api/auth         → auth.py       (register, login)    │
│  /api/admin        → admin.py      (admin management)   │
│  /api/company      → company.py    (company operations) │
│  /api/student      → student.py    (student profile)    │
│  /api/drives       → placement_drive.py (drive listing) │
│  /api/applications → application.py   (apply, history)  │
│                                                          │
│  Flask-JWT-Extended · Flask-SQLAlchemy · Flask-Caching  │
│  Flask-CORS · Flask-Bcrypt · Werkzeug                   │
└──────┬───────────────────────────────┬──────────────────┘
       │                               │
┌──────▼──────┐               ┌────────▼────────┐
│   SQLite DB  │               │     Redis        │
│  instance/   │               │  DB 0: Celery    │
│  launchpad.db│               │  DB 1: API Cache │
└─────────────┘               └────────┬────────┘
                                        │
                               ┌────────▼────────┐
                               │  Celery Workers  │
                               │  + Beat Scheduler│
                               │                  │
                               │  • Daily reminder│
                               │  • Monthly report│
                               │  • CSV export    │
                               └────────┬────────┘
                                        │
                               ┌────────▼────────┐
                               │    MailHog       │
                               │  SMTP: port 1025 │
                               │  Web UI: port 8025│
                               └─────────────────┘
```

---

## 3. Three-Role System & Business Logic

### 3.1 Admin — Institute Placement Cell

The admin is a **single pre-seeded superuser** — there is no admin registration endpoint. The admin account is created automatically when the database is initialized for the first time.

**Admin responsibilities and workflow:**

#### Company Approval Workflow

1. A company registers on the platform. Their account is immediately set to `approval_status: pending`.
2. The admin reviews the company registration on the **Admin → Companies** page.
3. The admin can:
   - **Approve** → Company can now log in and create placement drives.
   - **Reject** → Company cannot log in (login returns 403).
   - **Blacklist** → Toggles blacklist status. Blacklisting a pending company auto-sets their status to `rejected`. Un-blacklisting resets status to `pending` so the admin can re-review.

#### Placement Drive Approval Workflow

1. An approved company creates a placement drive. The drive starts as `status: pending`.
2. The admin reviews drives on the **Admin → Drives** page.
3. The admin can:
   - **Approve** → Drive becomes visible to eligible students on their dashboard.
   - **Reject** → Drive is hidden from students.

#### Student Management

- Admin can view all registered students, search by name/email/branch.
- Admin can **blacklist** a student (toggle). A blacklisted student cannot log in.
- Admin can view a specific student's full application history.

#### Dashboard & Reports

- Dashboard shows aggregate stats: total students, total companies, total placement drives.
- Admin can view **all applications** across all students and drives.
- Admin can manually trigger background jobs for demo purposes:
  - **Send Daily Reminders** — immediately queues the daily reminder Celery task.
  - **Send Monthly Report** — immediately queues the monthly report Celery task.

---

### 3.2 Company

Companies self-register but **cannot use the platform until the admin approves them**. Attempting to log in before approval returns a 403 error with a clear message.

**Company workflow:**

#### Registration

1. Company fills in: email, password, company name, HR contact email, website, description.
2. Account is created with `approval_status: pending`.
3. Company cannot log in until admin approves.

#### After Approval

1. Company logs in and sees their **Dashboard** — company profile info + all their drives with applicant counts.
2. Company can update their profile (name, HR email, website, description).

#### Placement Drive Management

1. Company creates a drive with:
   - Job title, job description
   - Eligibility criteria: eligible branches (e.g., `["CS", "ECE"]`), minimum CGPA, eligible years (e.g., `[3, 4]`)
   - Application deadline (ISO datetime)
2. Drive starts as `pending` — admin must approve before students can see it.
3. While a drive is still `pending`, the company can **edit** it (job title, description, deadline, eligibility).
4. Once approved, the company can **close** the drive (sets status to `closed`, stops new applications).

#### Application Management

1. Company views all applications for each drive on the **Drive Detail** page.
2. For each applicant, the company can update the application status:
   - `shortlisted` — Student is shortlisted for interview.
   - `selected` — Student is selected/offered the position.
   - `rejected` — Student is rejected.
   - (Note: Cannot set back to `applied` — only forward progression.)

---

### 3.3 Student

Students self-register and can immediately log in (no approval required).

**Student workflow:**

#### Registration & Profile

1. Student registers with: email, password, full name, branch, CGPA, year.
2. Student can update their profile at any time.
3. Student can upload a resume (PDF, DOC, or DOCX, max 5 MB). The file is stored on the server and the path is saved in the database.
4. Student can delete their uploaded resume.

#### Applying to Drives

1. Student's **Dashboard** shows all approved placement drives.
2. Each drive card shows an **eligibility badge** — whether the student is eligible based on their current profile (branch, CGPA, year).
3. Student can filter/search drives by job title, company name, branch, year, or CGPA.
4. When a student clicks **Apply**, the server performs these checks in order:
   1. Drive must be `approved` (not pending/rejected/closed).
   2. Application deadline must not have passed.
   3. Student's branch must be in the drive's `eligible_branches` (if set).
   4. Student's CGPA must be ≥ `min_cgpa` (if set).
   5. Student's year must be in `eligible_years` (if set).
   6. Student must not have already applied to this drive (unique constraint).
5. If all checks pass, an application is created with `status: applied`.

#### Tracking Applications

1. Student views all their applications on the **My Applications** page.
2. Each row shows: company name, job title, application status, applied date, last updated.
3. Student can **export their placement history** as a CSV file — this triggers an async Celery job that generates the CSV and emails it to the student.

---

## 4. Core Business Rules

1. **Single admin** — Only one admin exists, created programmatically at DB initialization. No admin registration endpoint.
2. **Company approval gate** — Companies cannot create drives or access any company features until the admin approves their registration.
3. **Drive approval gate** — Placement drives are invisible to students until the admin approves them.
4. **Eligibility validation is server-side** — Even if the frontend shows a drive as eligible, the backend re-validates all eligibility criteria on every application submission.
5. **No duplicate applications** — A student can apply to a given drive exactly once. Enforced by both a database `UniqueConstraint` and an application-level check (returns 409 Conflict).
6. **Deadline enforcement** — Applications are rejected if the current UTC time is past the drive's `application_deadline`.
7. **Blacklist is a toggle** — Blacklisting a user/company is reversible. Un-blacklisting a company resets their `approval_status` to `pending` so the admin can re-approve.
8. **Company can only edit pending drives** — Once a drive is approved or rejected, it cannot be edited by the company.
9. **Company can only close approved drives** — A drive must be `approved` before it can be closed.
10. **Application status is forward-only** — Companies can only set application status to `shortlisted`, `selected`, or `rejected`. They cannot revert an application back to `applied`.
11. **Resume file naming** — Uploaded resumes are stored as `student_{id}_{original_filename}` to prevent collisions.
12. **JWT tokens expire in 24 hours** — Stored in `localStorage` under keys `token`, `role`, `email`.
13. **Cache TTL is 5 minutes** — All cached responses expire after 300 seconds. Write operations invalidate relevant cache keys immediately.

---

## 5. Data Models

```
User
├── id (PK)
├── email (unique, indexed)
├── password_hash
├── role: "admin" | "company" | "student"
├── is_blacklisted (bool, default false)
└── created_at

StudentProfile (1:1 with User where role="student")
├── id (PK)
├── user_id (FK → users.id, unique)
├── full_name
├── branch (e.g., "CS", "ECE", "ME")
├── cgpa (float, 0.0–10.0)
├── year (int, 1–4)
└── resume_path (nullable, relative path)

CompanyProfile (1:1 with User where role="company")
├── id (PK)
├── user_id (FK → users.id, unique)
├── company_name
├── hr_contact_email (nullable)
├── website (nullable)
├── description (nullable)
└── approval_status: "pending" | "approved" | "rejected" | "blacklisted"*

PlacementDrive (many:1 with CompanyProfile)
├── id (PK)
├── company_id (FK → company_profiles.id)
├── job_title
├── job_description (nullable)
├── eligible_branches (CSV string, e.g., "CS,ECE,IT" — null = no restriction)
├── min_cgpa (float, nullable — null = no restriction)
├── eligible_years (CSV string, e.g., "3,4" — null = no restriction)
├── application_deadline (datetime)
├── status: "pending" | "approved" | "rejected" | "closed"
└── created_at

Application (many:1 with StudentProfile, many:1 with PlacementDrive)
├── id (PK)
├── student_id (FK → student_profiles.id)
├── drive_id (FK → placement_drives.id)
├── status: "applied" | "shortlisted" | "selected" | "rejected"
├── applied_at
└── updated_at
    UniqueConstraint(student_id, drive_id)
```

> \* `CompanyProfile.approval_status` is stored in the `company_profiles` table. The `is_blacklisted` flag lives on the `User` model. When a company is blacklisted, `User.is_blacklisted = True` and `CompanyProfile.approval_status` is set to `"rejected"` if it was `"pending"`.

---

## 6. Status Lifecycles

### Company Approval Status

```
pending ──[admin approve]──► approved
pending ──[admin reject]───► rejected
pending ──[admin blacklist]─► rejected  (+ is_blacklisted = true)
approved ──[admin blacklist]─► (is_blacklisted = true, approval_status unchanged)
any ──[admin un-blacklist]──► pending   (is_blacklisted = false, approval_status = "pending")
```

### Placement Drive Status

```
pending ──[admin approve]──► approved
pending ──[admin reject]───► rejected
approved ──[company close]──► closed
```

### Application Status

```
applied ──[company action]──► shortlisted
applied ──[company action]──► rejected
shortlisted ──[company action]──► selected
shortlisted ──[company action]──► rejected
```

---

## 7. Tech Stack

### Backend

| Technology         | Version              | Purpose                                    |
| ------------------ | -------------------- | ------------------------------------------ |
| Python             | 3.12+                | Runtime                                    |
| Flask              | ≥3.0.0               | REST API framework                         |
| Flask-SQLAlchemy   | ≥3.1.0               | ORM                                        |
| Flask-JWT-Extended | ≥4.6.0               | JWT authentication                         |
| Flask-Caching      | ≥2.3.0               | Redis-backed response caching              |
| Flask-CORS         | ≥4.0.0               | Cross-origin resource sharing              |
| Flask-Bcrypt       | ≥1.0.1               | Password hashing (bcrypt)                  |
| Celery             | ≥5.3.0               | Background task queue                      |
| Redis              | ≥5.0.0               | Celery broker + result backend + API cache |
| Werkzeug           | ≥3.0.0               | Secure file upload handling                |
| Jinja2             | (bundled with Flask) | Email HTML template rendering **only**     |
| `uv`               | latest               | Python package manager                     |

### Frontend

| Technology         | Version     | Purpose                                 |
| ------------------ | ----------- | --------------------------------------- |
| Vue 3              | ^3.2.13     | UI framework                            |
| Vue Router         | ^4.0.3      | Client-side routing (hash history mode) |
| Vue CLI            | ~5.0.0      | Build tooling                           |
| Bootstrap          | 5.3.8 (CDN) | CSS framework                           |
| Native `fetch` API | built-in    | HTTP client (no axios)                  |

### Infrastructure

| Service | Purpose                                 | Port                                  |
| ------- | --------------------------------------- | ------------------------------------- |
| SQLite  | Primary database                        | file: `backend/instance/launchpad.db` |
| Redis   | Celery broker (DB 0) + API cache (DB 1) | 6379                                  |
| MailHog | Local SMTP server for email testing     | SMTP: 1025, Web UI: 8025              |

---

## 8. Prerequisites

- **Python 3.12+**
- **Node.js** (LTS) + **npm**
- **Docker** (for Redis and MailHog)
- **`uv`** Python package manager — install via `pip install uv` or see [uv docs](https://docs.astral.sh/uv/)

---

## 9. Setup & Running

All services must be running simultaneously. Open separate terminal windows for each.

### Step 1 — Start Redis (Docker)

```bash
docker run -d -p 6379:6379 --name launchpad-redis redis
```

### Step 2 — Start MailHog (Docker)

```bash
docker run -d -p 1025:1025 -p 8025:8025 --name launchpad-mailhog mailhog/mailhog
```

MailHog web UI (view sent emails): http://localhost:8025

### Step 3 — Start Flask Backend (port 5000)

```bash
cd backend
uv sync
uv run python main.py
```

The database (`backend/instance/launchpad.db`) and the admin user are created automatically on first run.

### Step 4 — Start Celery Worker

```bash
cd backend
uv run celery -A src.workers.workers worker --loglevel=info
```

### Step 5 — Start Celery Beat Scheduler

```bash
cd backend
uv run celery -A src.workers.workers beat --loglevel=info
```

### Step 6 — Start Vue Frontend (port 8080)

```bash
cd frontend
npm install
npm run serve
```

Frontend: http://localhost:8080

### Step 7 — (Optional) Seed Test Data

```bash
cd backend
uv run python tests/scripts/seed_data.py
```

This creates 6 companies, 12 students, 10 placement drives, and 32 applications for testing.

---

## 10. Default Credentials

### Admin (pre-seeded)

| Field    | Value                 |
| -------- | --------------------- |
| Email    | `admin@launchpad.com` |
| Password | `admin123`            |
| Role     | `admin`               |

### Test Data (after running seed script)

The seed script creates companies with emails like `hr@techcorp.com` (password: `password123`) and students like `alice@student.com` (password: `password123`). Check `backend/tests/scripts/seed_data.py` for the full list.

---

## 11. Background Jobs (Celery)

LaunchPad uses Celery with Redis as the broker for three background tasks:

### Task 1: Daily Deadline Reminders (Scheduled)

- **Schedule**: Every day at **8:00 AM UTC** (Celery Beat)
- **What it does**:
  1. Queries all `approved` placement drives with `application_deadline` within the next 3 days.
  2. For each such drive, finds all eligible students who have **not yet applied**.
  3. Skips blacklisted students.
  4. Sends a personalized HTML reminder email to each eligible student via MailHog.
- **Email template**: `backend/src/templates/email/daily_reminder.html`
- **Manual trigger** (admin only): `POST /api/admin/trigger/daily-reminders`

### Task 2: Monthly Activity Report (Scheduled)

- **Schedule**: **1st of every month at 7:00 AM UTC** (Celery Beat)
- **What it does**:
  1. Computes stats for the **previous calendar month**: drives created, applications submitted, students selected.
  2. Computes all-time totals: students, companies, drives, applications, selections.
  3. Lists the top 5 drives by applicant count (all time).
  4. Renders an HTML report and emails it to the admin (`admin@launchpad.com`).
- **Email template**: `backend/src/templates/email/monthly_report.html`
- **Manual trigger** (admin only): `POST /api/admin/trigger/monthly-report`

### Task 3: CSV Export (User-Triggered)

- **Trigger**: Student clicks "Export History" → `POST /api/applications/export`
- **What it does**:
  1. Generates a CSV of the student's complete application history.
  2. CSV columns: Student ID, Student Name, Company Name, Job Title, Drive Status, Application Status, Applied Date, Last Updated.
  3. Attaches the CSV to a notification email and sends it to the student.
- **Email template**: `backend/src/templates/email/csv_export_done.html`
- **Response**: Returns HTTP 202 immediately with a `task_id`. The email arrives asynchronously.

---

## 12. Frontend Routes

All routes use **hash history mode** (`/#/path`). Role-based navigation guards redirect unauthenticated or unauthorized users to `/login`.

| Path                               | Component                | Access       |
| ---------------------------------- | ------------------------ | ------------ |
| `/login`                           | LoginView                | Public       |
| `/register/student`                | RegisterStudentView      | Public       |
| `/register/company`                | RegisterCompanyView      | Public       |
| `/admin/dashboard`                 | AdminDashboard           | Admin only   |
| `/admin/companies`                 | AdminCompanies           | Admin only   |
| `/admin/students`                  | AdminStudents            | Admin only   |
| `/admin/students/:id/applications` | AdminStudentApplications | Admin only   |
| `/admin/drives`                    | AdminDrives              | Admin only   |
| `/admin/applications`              | AdminApplications        | Admin only   |
| `/company/dashboard`               | CompanyDashboard         | Company only |
| `/company/drives`                  | CompanyDrives            | Company only |
| `/company/drives/new`              | CompanyCreateDrive       | Company only |
| `/company/drives/:id`              | CompanyDriveDetail       | Company only |
| `/student/dashboard`               | StudentDashboard         | Student only |
| `/student/profile`                 | StudentProfile           | Student only |
| `/student/applications`            | StudentApplications      | Student only |

---

## 13. API Overview

Base URL: `http://localhost:5000`

All protected endpoints require the header:

```
Authorization: Bearer <JWT_TOKEN>
```

### Authentication (`/api/auth`)

| Method | Endpoint                     | Auth | Description                     |
| ------ | ---------------------------- | ---- | ------------------------------- |
| POST   | `/api/auth/register/student` | None | Register a new student          |
| POST   | `/api/auth/register/company` | None | Register a new company          |
| POST   | `/api/auth/login`            | None | Login — returns JWT token       |
| GET    | `/api/auth/me`               | Any  | Get current user info + profile |

### Admin (`/api/admin`) — Admin JWT required

| Method | Endpoint                                | Description                                   |
| ------ | --------------------------------------- | --------------------------------------------- |
| GET    | `/api/admin/dashboard`                  | Aggregate stats (students, companies, drives) |
| GET    | `/api/admin/companies`                  | List companies (`?status=`, `?search=`)       |
| GET    | `/api/admin/companies/<id>`             | Get single company                            |
| PATCH  | `/api/admin/companies/<id>/approve`     | Approve company registration                  |
| PATCH  | `/api/admin/companies/<id>/reject`      | Reject company registration                   |
| PATCH  | `/api/admin/companies/<id>/blacklist`   | Toggle company blacklist                      |
| GET    | `/api/admin/students`                   | List students (`?search=`)                    |
| GET    | `/api/admin/students/<id>`              | Get single student                            |
| PATCH  | `/api/admin/students/<id>/blacklist`    | Toggle student blacklist                      |
| GET    | `/api/admin/students/<id>/applications` | Get student's application history             |
| GET    | `/api/admin/drives`                     | List all drives (`?status=`)                  |
| PATCH  | `/api/admin/drives/<id>/approve`        | Approve placement drive                       |
| PATCH  | `/api/admin/drives/<id>/reject`         | Reject placement drive                        |
| GET    | `/api/admin/applications`               | List all applications (all students)          |
| POST   | `/api/admin/trigger/daily-reminders`    | Manually trigger daily reminder job           |
| POST   | `/api/admin/trigger/monthly-report`     | Manually trigger monthly report job           |

### Company (`/api/company`) — Approved Company JWT required

| Method | Endpoint                                | Description                                     |
| ------ | --------------------------------------- | ----------------------------------------------- |
| GET    | `/api/company/dashboard`                | Company info + all drives with applicant counts |
| GET    | `/api/company/profile`                  | Get company profile                             |
| PUT    | `/api/company/profile`                  | Update company profile                          |
| GET    | `/api/company/drives`                   | List company's placement drives                 |
| POST   | `/api/company/drives`                   | Create a new placement drive                    |
| GET    | `/api/company/drives/<id>`              | Get single drive                                |
| PUT    | `/api/company/drives/<id>`              | Edit drive (pending drives only)                |
| PATCH  | `/api/company/drives/<id>/close`        | Close an approved drive                         |
| GET    | `/api/company/drives/<id>/applications` | List all applications for a drive               |
| PATCH  | `/api/company/applications/<id>/status` | Update application status                       |

### Student (`/api/student`) — Student JWT required

| Method | Endpoint                      | Description                                        |
| ------ | ----------------------------- | -------------------------------------------------- |
| GET    | `/api/student/profile`        | Get student profile                                |
| PUT    | `/api/student/profile`        | Update student profile                             |
| POST   | `/api/student/profile/resume` | Upload resume (multipart/form-data, key: `resume`) |
| DELETE | `/api/student/profile/resume` | Delete uploaded resume                             |
| GET    | `/api/student/applications`   | Get student's application history                  |

### Drives (`/api/drives`) — Any authenticated user

| Method | Endpoint           | Description                                                                                 |
| ------ | ------------------ | ------------------------------------------------------------------------------------------- |
| GET    | `/api/drives`      | List approved drives with eligibility info (`?search=`, `?branch=`, `?year=`, `?min_cgpa=`) |
| GET    | `/api/drives/<id>` | Get drive details with eligibility info                                                     |

### Applications (`/api/applications`) — Student JWT required

| Method | Endpoint                   | Description                            |
| ------ | -------------------------- | -------------------------------------- |
| POST   | `/api/applications`        | Apply to a placement drive             |
| GET    | `/api/applications/<id>`   | Get single application detail          |
| POST   | `/api/applications/export` | Trigger async CSV export (returns 202) |

For the complete OpenAPI 3.0 specification with all request/response schemas, see [`api.yaml`](./api.yaml).

---

## 14. Seed Data

Run the seed script to populate the database with realistic test data:

```bash
cd backend
uv run python tests/scripts/seed_data.py
```

**What it creates:**

- 6 companies (all approved)
- 12 students (various branches, CGPAs, years)
- 10 placement drives (mix of approved, pending, closed)
- 32 applications (various statuses)

**Other test scripts:**

- `tests/scripts/test_api.py` — API endpoint tests
- `tests/scripts/test_frontend.py` — Playwright-based frontend tests
- `tests/scripts/trigger_daily_mail.py` — Manually trigger the daily reminder email

---

## 15. Environment Variables

All variables have sensible defaults for local development. Override via environment variables for production.

| Variable                | Default                           | Description                           |
| ----------------------- | --------------------------------- | ------------------------------------- |
| `SECRET_KEY`            | `dev-secret-key-change-in-prod`   | Flask secret key                      |
| `JWT_SECRET_KEY`        | `jwt-secret-key-change-in-prod`   | JWT signing key                       |
| `DATABASE_URL`          | `sqlite:///instance/launchpad.db` | SQLAlchemy database URI               |
| `REDIS_CACHE_URL`       | `redis://localhost:6379/1`        | Redis URL for Flask-Caching           |
| `CELERY_BROKER_URL`     | `redis://localhost:6379/0`        | Redis URL for Celery broker           |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/0`        | Redis URL for Celery results          |
| `MAIL_SERVER`           | `localhost`                       | SMTP server host                      |
| `MAIL_PORT`             | `1025`                            | SMTP server port                      |
| `ADMIN_EMAIL`           | `admin@launchpad.com`             | Admin email (for seeding + reports)   |
| `ADMIN_PASSWORD`        | `admin123`                        | Admin password (used only at DB init) |

---

## 16. Project Structure

```
mad2-placement-portal-application-v2/
│
├── README.md                       ← This file
├── api.yaml                        ← OpenAPI 3.0 specification
│
├── backend/                        ← Flask REST API
│   ├── main.py                     ← Entry point
│   ├── pyproject.toml              ← uv project config + dependencies
│   ├── .python-version             ← Python 3.12 pin
│   ├── instance/
│   │   └── launchpad.db            ← SQLite database (auto-created)
│   └── src/
│       ├── app.py                  ← Flask app factory + config + admin seeding
│       ├── models.py               ← SQLAlchemy models (5 models)
│       ├── apis/
│       │   ├── auth.py             ← /api/auth blueprint
│       │   ├── admin.py            ← /api/admin blueprint
│       │   ├── company.py          ← /api/company blueprint
│       │   ├── student.py          ← /api/student blueprint
│       │   ├── placement_drive.py  ← /api/drives blueprint
│       │   └── application.py      ← /api/applications blueprint
│       ├── workers/
│       │   ├── workers.py          ← Celery app + Beat schedule
│       │   ├── task.py             ← 3 Celery task definitions
│       │   └── mailer.py           ← smtplib email utility (MailHog)
│       ├── static/
│       │   └── uploads/resumes/    ← Uploaded student resumes
│       └── templates/email/
│           ├── daily_reminder.html ← Jinja2 deadline reminder template
│           ├── monthly_report.html ← Jinja2 monthly report template
│           └── csv_export_done.html← Jinja2 CSV export notification template
│
├── frontend/                       ← Vue 3 SPA
│   ├── package.json
│   ├── vue.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api/index.js            ← Centralized fetch-based API helper
│       ├── router/index.js         ← Routes + role-based navigation guards
│       ├── components/NavBar.vue   ← Role-aware navbar
│       └── views/
│           ├── LoginView.vue
│           ├── RegisterStudentView.vue
│           ├── RegisterCompanyView.vue
│           ├── admin/              ← Admin views (Dashboard, Companies, Students, Drives, Applications)
│           ├── company/            ← Company views (Dashboard, Drives, CreateDrive, DriveDetail)
│           └── student/            ← Student views (Dashboard, Profile, Applications)
│
├── memory-bank/                    ← Project documentation
│   ├── projectbrief.md
│   ├── productContext.md
│   ├── activeContext.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── progress.md
│
└── reset_db.ps1                    ← PowerShell script to reset the database
```

---

## Quick Start (TL;DR)

```bash
# Terminal 1 — Redis
docker run -d -p 6379:6379 redis

# Terminal 2 — MailHog
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Terminal 3 — Flask backend
cd backend && uv sync && uv run python main.py

# Terminal 4 — Celery worker
cd backend && uv run celery -A src.workers.workers worker --loglevel=info

# Terminal 5 — Celery Beat
cd backend && uv run celery -A src.workers.workers beat --loglevel=info

# Terminal 6 — Vue frontend
cd frontend && npm install && npm run serve

# Terminal 7 — Seed data (optional, run once)
cd backend && uv run python tests/scripts/seed_data.py
```

Then open http://localhost:8080 and log in as `admin@launchpad.com` / `admin123`.
