# Email Dashboard & Automation Tool

Phase 1 provides a Docker-first project skeleton with:

- A FastAPI backend on port `8000`
- A React frontend on port `3000`
- Volume-based local development for fast iteration
- A backend settings layer ready to read from `backend/.env`

## Startup

1. Copy `backend/.env.example` to `backend/.env`
2. Run `docker compose up --build`
3. Open `http://localhost:3000` for the frontend
4. Open `http://localhost:8000/docs` for the backend API docs

## Notes

- No email delivery logic is implemented yet
- No database is included yet
- The structure is intentionally simple so future phases can add scheduling, bulk sending, dashboards, and tracking cleanly
