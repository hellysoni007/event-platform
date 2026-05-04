# Event Platform Backend

Backend API for seekers and facilitators to manage events and enrollments, built with Django, DRF, PostgreSQL, JWT auth, OTP verification, and Celery-based notifications.

## Tech Stack

- Django + Django REST Framework
- PostgreSQL
- Redis + Celery (worker/beat)
- SimpleJWT
- Pytest
- Docker Compose

## Setup

1. Copy env file:
   - `copy .env.example .env` (Windows)
2. Install dependencies:
   - `python -m pip install -r requirements.txt`
3. Run migrations:
   - `python manage.py migrate`
4. Start API:
   - `python manage.py runserver`

## Docker Local Run

1. Create `.env` from `.env.example`.
2. Run:
   - `docker compose up --build`
3. API base:
   - `http://localhost:8000/api/v1/`

## Environment Variables

See `.env.example` for:
- Django runtime config
- Postgres connection
- Redis URL
- JWT lifetimes
- Email backend settings
- Sentry DSN

## API Design Decisions

- Default Django `User` model retained.
- `username` generated internally and hidden from API.
- Signup uses `email/password/role` with OTP verification before login.
- JWT access + refresh with rotation.
- RBAC with role + ownership checks.
- Event soft delete (`is_deleted`/`deleted_at`).
- Enrollment consistency with row lock and `enrolled_count` atomic updates.
- Pagination shape: `count`, `next`, `previous`, `results`.
- Error shape: `{ "detail": "...", "code": "..." }`.

## Tests

- Run all tests:
  - `pytest`
- Test structure:
  - `tests/unit/`
  - `tests/integration/`

## Tradeoffs

- Search uses ORM-based filtering and text matching for MVP; can migrate to PostgreSQL full-text search for higher scale.
- Email tasks are asynchronous via Celery; for stronger delivery guarantees, provider webhooks and retry dead-letter handling can be added.
- SQLite works for local quick start; PostgreSQL is the production/CI target.

## Postman Collection

- `postman_collection.json`
