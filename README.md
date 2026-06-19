# CleanOps Backend — Cleaning Operations System API

Standalone **Django REST Framework** backend for the CleanOps Cleaning Operations Management System.

**Frontend (Angular):** [`cleaning-operations-system`](../cleaning-operations-system)

## Tech Stack

- Python 3.11+
- Django 6
- Django REST Framework
- Simple JWT authentication
- SQLite (development) — swap to PostgreSQL for production
- CORS enabled for Angular (`http://localhost:4200`)

## Quick Start

```bash
cd cleaning-operations-system-backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo_data
python manage.py runserver
```

API base URL: **http://127.0.0.1:8000/api/**

Admin panel: **http://127.0.0.1:8000/admin/**

## Demo Accounts

| Role       | Email                    | Password      |
|------------|--------------------------|---------------|
| Admin      | admin@cleanops.com       | admin123      |
| Supervisor | supervisor@cleanops.com  | supervisor123 |
| Cleaner    | cleaner@cleanops.com     | cleaner123    |

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | Login (returns JWT + user) |
| POST | `/api/auth/refresh/` | Refresh JWT token |
| GET | `/api/auth/me/` | Current user profile |
| POST | `/api/auth/password-reset/` | Request password reset |
| GET/POST | `/api/auth/users/` | List/create users |

### Cleaners
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/cleaners/` | List/create cleaners |
| GET/PATCH/DELETE | `/api/cleaners/{id}/` | Cleaner detail (id = user id) |
| POST | `/api/cleaners/{id}/deactivate/` | Deactivate cleaner |

### Rooms
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/rooms/` | List/create rooms |
| GET/PATCH/DELETE | `/api/rooms/{id}/` | Room detail |
| GET | `/api/rooms/by-qr/{qr_code}/` | Lookup room by QR code |
| PATCH | `/api/rooms/{id}/status/` | Update room status |

### Assignments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/assignments/` | List assignments (`?cleanerId=`) |
| POST | `/api/assignments/bulk-assign/` | Assign rooms to cleaner |
| POST | `/api/assignments/{id}/reassign/` | Reassign to another cleaner |

### Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks/` | List tasks (`?cleanerId=`, `?status=`) |
| GET | `/api/tasks/pending-verification/` | Tasks awaiting verification |
| POST | `/api/tasks/from-assignment/` | Create task from assignment |
| POST | `/api/tasks/{id}/start/` | Start task (QR + GPS) |
| POST | `/api/tasks/{id}/before-photo/` | Upload before photo |
| POST | `/api/tasks/{id}/after-photo/` | Upload after photo |
| POST | `/api/tasks/{id}/complete/` | Mark task complete |
| POST | `/api/tasks/{id}/verify/` | Supervisor verify task |

### Attendance
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/attendance/` | List records (`?cleanerId=`) |
| GET | `/api/attendance/today/{cleaner_id}/` | Today's record |
| POST | `/api/attendance/check-in/` | Check in with GPS |
| POST | `/api/attendance/check-out/` | Check out with GPS |

### Dashboard & Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats/` | Dashboard KPIs |
| GET | `/api/dashboard/weekly-completion/` | Weekly chart data |
| GET | `/api/reports/performance/` | Cleaner performance reports |
| POST | `/api/reports/export/` | Export report (mock) |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/` | User notifications |
| PATCH | `/api/notifications/{id}/read/` | Mark as read |

## Authentication

All endpoints except login, refresh, and password-reset require a JWT Bearer token:

```
Authorization: Bearer <access_token>
```

Login response includes `token` (access), `refresh`, and `user` objects in camelCase.

## Environment Variables

Copy `.env.example` to `.env`:

```
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:4200
```

## Project Structure

```
cleaning-operations-system-backend/
├── config/           # Django project settings
├── accounts/         # User model, auth, cleaner profiles
├── operations/       # Rooms, tasks, attendance, notifications
├── manage.py
└── requirements.txt
```

## Connecting the Angular Frontend

In the frontend project (`cleaning-operations-system`), update `src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://127.0.0.1:8000/api',
};
```

Replace mock services in `src/app/core/services/` with HTTP calls to these endpoints.
