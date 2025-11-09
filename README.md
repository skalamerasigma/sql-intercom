# Support Queue Live (SQL)

Modern FastAPI dashboard to visualize live support metrics for Intercom team `5480079` using Intercom's REST API.

## Features
- Fetches admins (API Call #1: `GET /admins`) and conversations (API Call #2: `POST /conversations/search`) with full pagination.
- Filters admins by team membership since `/admins` cannot filter by team id.
- KPIs: Open, Snoozed, Unassigned, Waiting for first reply.
- Metrics: Average/P95 wait time, SLA first response adherence, ratings summary.
- Agent table with assignment counts and away/inbox-seat flags.
- Auto-refresh (default every 30s) and themed UI using the provided color palette.

## Setup
1. Python 3.10+
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set environment variables (recommended via `.env` in the project root). Do NOT commit secrets to git.

```bash
# .env
INTERCOM_BEARER_TOKEN="<your_intercom_bearer_token>"
INTERCOM_TEAM_ID=5480079
SLA_FIRST_RESPONSE_MINUTES=15
REFRESH_INTERVAL_SECONDS=30
PER_PAGE=150
```

> If you prefer, export variables in your shell instead of using `.env`.

## Run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` for the dashboard.

## Notes on Intercom API usage
- Authorization is Bearer token (provided above). This is read from `INTERCOM_BEARER_TOKEN`.
- Pagination:
  - `/conversations/search`: uses `pagination.per_page` and `starting_after` from `pages.next.starting_after`.
  - `/admins`: best-effort pagination; if `pages.next.starting_after` exists, it will iterate until all pages are fetched.
- Team filtering:
  - Admins are filtered by `team_ids` or `team_priority_level.primary_team_ids` matching `INTERCOM_TEAM_ID`.
- SLA:
  - First response SLA is computed from `statistics.first_admin_reply_at - waiting_since` and compared to `SLA_FIRST_RESPONSE_MINUTES`.

## Customize
- Update palette or refresh cadence in `static/styles.css` and `intercom_dashboard/config.py` respectively.
- Add additional metrics in `intercom_dashboard/metrics.py` and expose them from `/api/metrics`.

## Security
- Do not commit your real `.env`. Use environment variables in deployment.


# sql-intercom
