# ValBelluna Motorsport

Kart association calendar app — Flask 3.1, SQLAlchemy 2.0, Flask-JWT-Extended, Jinja2 + HTMX 2.0 + Alpine.js 3.14 + Tailwind CSS (CDN). Deployed on PythonAnywhere. Python 3.14 (pyright). Rewritten from FastAPI → Flask (see `docs/rewrite-log.md`).

## Quick start

```bash
./start.sh                 # .venv/bin/python run.py → :8000
.venv/bin/python run.py    # debug mode, host 0.0.0.0
```

## Verification pipeline (run in order)

```bash
.venv/bin/ruff check app/ tests/
.venv/bin/ruff format --check app/ tests/
.venv/bin/pyright
.venv/bin/python -m pytest tests/ -v
```

## Architecture

| Blueprint | Prefix | Key routes |
|-----------|--------|------------|
| `auth` | `/auth` | GET/POST login, logout, register, settings, change-password/email, admin change-credentials, token generation, admin delete user |
| `races` | `/races` | Calendar (year filter), detail, CRUD, admin dashboard/members/types, export (superadmin), import (superadmin) |
| `participation` | `/participation` | Set status, update note, toggle macchina, admin override |
| `reports` | `/reports` | Aggregate stats (admin-only, filters `ruolo != "superadmin"`) |
| `history` | `/history` | Last 200 audit logs, export JSON (superadmin, no row limit) |

- **Vanilla SQLAlchemy** (not Flask-SQLAlchemy): `Base`, `engine`, `SessionLocal`, `get_db()` context manager in `app/database.py`
- **DELETE journal mode** (not WAL) — PythonAnywhere NFS compatibility
- `before_request` auto-creates `Base.metadata.create_all` + default admin/superadmin on first request
- **APScheduler** (`app/tasks.py`) defines `start_scheduler()`/`stop_scheduler()` but is **never called** in the app factory — not wired into startup

## Auth & roles

- `@jwt_required()` / `@admin_required` (admin+superadmin) / `@superadmin_required` / `@optional_auth`
- `@jwt_required` is a **local wrapper** (`app/auth.py`), not `flask_jwt_extended`'s directly
- `JWT_TOKEN_LOCATION = ["headers", "cookies"]` — Bearer requests skip CSRF, cookie-only requests require CSRF
- Login sets both JSON body + httpOnly cookie
- Defaults: `admin@valbellunamotorsport.it` / `admin123`, `superadmin@valbellunamotorsport.it` / `superadmin123`
- SuperAdmin hidden from all member/participant/report/dashboard queries (`User.ruolo != "superadmin"`)
- Registration tokens stored in-memory in `app/blueprints/auth.py:20` — **lost on restart**

## Database quirks

- `User.attivo` and `Participation.con_macchina` are `Integer(0/1)`, not bool
- `Race.data_inizio` and `Race.data_fine` are nullable (`NULL` = no date / single-day)
- `scadenza_conferma` checked against `datetime.now(UTC).date()` in participation routes
- Calendar view uses `func.strftime("%Y", Race.data_inizio)` — SQLite-specific, not portable
- Alembic migrations exist (`alembic/versions/`) but `before_request` auto-creates tables, so migrations are optional
- All user emails use `@valbellunamotorsport.it` domain, generated from `User.nome` (lowercased, spaces → dots)

## Templates

- All URLs are **hardcoded** (no `url_for`) — match blueprint `url_prefix` exactly
- **File upload** (import backup) uses native `fetch()` + `FormData` + `Authorization: Bearer` header — HTMX can't handle multipart file upload
- Import route returns `"error"` key on failure; all other JSON routes return `"detail"`

## CLI (`python -m app.cli <command>`)

```
list-users                        reset-password <email> [--password]
make-superadmin <email>           make-admin <email>
create-superadmin <email> <nome>  delete-user <email> [-y]
```

## Tests

- `tests/conftest.py` sets `DATABASE_URL=sqlite:///:memory:`, `SECRET_KEY`, `JWT_SECRET` **before** importing app
- Fixtures: `app` (session-scoped create_all/drop_all), `client`, `db`, `*_user`, `*_token`, `auth_headers`
- Token auth: `create_access_token(identity=str(user.id))` → pass as `Authorization: Bearer` header

## PythonAnywhere

```
git clone git@github.com:GiovanniChiarion/ValBellunaMotorsport.git
```

WSGI file at `/var/www/GChiarion_pythonanywhere_com_wsgi.py` — update path:
```python
sys.path.insert(0, '/home/GChiarion/ValBellunaMotorsport')
```
Static Web tab: `/static/` → `/home/GChiarion/ValBellunaMotorsport/app/static/`. Env vars: `DATABASE_URL`, `JWT_SECRET`, `SECRET_KEY`, `DEBUG=false`. Reload after every `git pull`.

## Seed

`python -m app.seed` reads `TEST Calendario 2026 Valbelluna Motorsport.xlsx` for bulk import. On PythonAnywhere the file doesn't exist → skips gracefully.
