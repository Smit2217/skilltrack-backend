# SkillTrack AI Backend

This is a small, modular FastAPI backend for the existing SkillTrack React frontend. It uses SQLAlchemy models and works with SQLite for a quick local start; set `DATABASE_URL` to a PostgreSQL connection string when deploying.

## 1. Start locally

```bash
cd skilltrack-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

## 2. PostgreSQL configuration

Set `DATABASE_URL` in `.env` to a value such as `postgresql+psycopg2://postgres:postgres@localhost:5432/skilltrack`. The included `docker-compose.yml` starts PostgreSQL locally. After the database is available, run `python seed.py` and then start FastAPI.

## 3. Authentication

Register with `POST /api/auth/register`, then log in with `POST /api/auth/login`. Send the returned token on protected requests as:

```http
Authorization: Bearer <access_token>
```

The student endpoints use the token to determine the current student. Faculty endpoints are intentionally simple for this first version and do not yet include faculty login or assignment tables.

## 4. Main endpoints

| Area | Endpoints |
|---|---|
| Authentication | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Student profile | `GET/PATCH /api/student/profile` |
| Skills | `GET /api/skills`, `GET/PUT /api/student/skills` |
| Portfolio | `GET/POST /api/student/projects`, `GET/POST /api/student/certifications` |
| Careers | `GET /api/careers`, `GET /api/careers/{id}/skills`, `PUT /api/student/career-goal` |
| Assessments | `POST/GET /api/student/assessments` |
| Analysis | `GET /api/student/skill-gaps`, `GET /api/student/roadmap` |
| Faculty | `GET /api/faculty/students`, student skills/progress/gaps, and `GET /api/faculty/students/low-progress` |

## 5. React connection

Create one API base URL in the frontend rather than repeating URLs throughout components:

```js
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function getProfile(token) {
  const response = await fetch(`${API_URL}/api/student/profile`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Could not load profile");
  return response.json();
}
```

Replace dashboard mock calls with equivalent functions for the endpoints above. Keep the existing visual components unchanged.

## Notes

The roadmap and skill-gap calculation are deliberately rule-based. A later version can add role-based faculty authentication, Alembic migrations, pagination, assignment relationships, and AI services without changing the core API shape.
