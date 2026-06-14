## aggiorna

Quando ti viene chiesto di aggiornare, esegui questo workflow:

1. Leggi AGENTS.md e i file blueprint (`app/blueprints/*.py`), `app/cli.py`, `app/models.py`, `app/config.py`
2. Confronta stato attuale del progetto con AGENTS.md:
   - Tabella blueprints: nuovi endpoint? permessi cambiati? (es. history è `@superadmin_required`)
   - Comandi CLI: modifiche/aggiunte? (es. `clear-logs`)
   - Sezioni App structure, Auth & roles, DB quirks, Templates, Verify
3. Se serve, aggiorna la documentazione (`docs`). Se viene aggiornata, genera anche i relativi pdf.
4. Se serve, riscrivi AGENTS.md con le modifiche
5. `git add -A`
6. `git commit -m "aggiorna: [breve sommario modifiche]"`
7. `git push`
8. Output riepilogo

---

# ValBelluna Motorsport

Kart association calendar app — Flask 3.1, SQLAlchemy 2.0, Flask-JWT-Extended, Jinja2 + HTMX 2.0 + Alpine.js 3.14 + Tailwind CSS (CDN). Deployed PythonAnywhere. Python 3.14 (pyright). FastAPI→Flask rewrite (`docs/rewrite-log.md`).

# Important 

- When a new feature is implemented, make sure it is documented in `docs/`. If txt files are modified, generate always also the relative pdfs.
- When a new feature is implemented, if not specified, implement it only for SuperAdmin as it is considered a beta-tester with all the powers of the Admin + other features. If in doubt, ask.

## Quick start

```bash
pip install -r requirements.txt         # .venv assumed
./start.sh                              # .venv/bin/python run.py → :8000
.venv/bin/python run.py                 # debug mode, host 0.0.0.0
```

Requires `.env` root:
```
DATABASE_URL="sqlite:///./calendario.db"
SECRET_KEY="dev-secret-key"
JWT_SECRET="dev-jwt-secret"
DEBUG=true
```

## Verify (order)

```bash
.venv/bin/ruff check app/ tests/
.venv/bin/ruff format --check app/ tests/
.venv/bin/pyright
.venv/bin/python -m pytest tests/ -v
```

## Blueprints

| Prefix | File | Does |
|--------|------|------|
| `/auth` | `blueprints/auth.py` | Login, logout, register, settings, change-password/email, `GET /me` (current user), admin change-credentials, token gen (`POST` with `expires_value`+`expires_unit`), token manage (`GET` list, `DELETE`, `PUT` expiry), token validate (`GET`), admin delete user |
| `/races` | `blueprints/races.py` | Calendar (year filter), detail, CRUD, admin dashboard/members/types, export (superadmin), import (superadmin) |
| `/participation` | `blueprints/participation.py` | Set status, update note, toggle macchina, admin override |
| `/reports` | `blueprints/reports.py` | Aggregate stats (admin-only, `ruolo != "superadmin"` filter) |
| `/history` | `blueprints/history.py` | Paginated audit log viewer with action/user/date/ip/race filters; export JSON (superadmin, no row limit) |

## App structure

- App factory: `app/__init__.py:create_app()` — called by `run.py` and tests with `test_config`
- Vanilla SQLAlchemy (no Flask-SQLAlchemy): `Base`, `engine`, `SessionLocal`, `get_db()` context manager in `app/database.py`
- **DELETE journal** (not WAL) — PythonAnywhere NFS compat
- `before_request` (×2): `initialize_db` — auto `Base.metadata.create_all` + default admin/superadmin on first request; `log_page_view` — logs every GET (except `/health`) to audit log, gated by `log_page_views` config
- APScheduler (`app/tasks.py`) defines `start_scheduler()`/`stop_scheduler()` — **never called** in app factory, not wired
- `/` → unauthenticated → login, authenticated → calendar. `/health` → JSON status.
- `pydantic-settings` (`app/config.py`) reads `.env` — `get_settings()` is `@lru_cache`d
- `opencode.json` has `"lsp": true` — pyright type-checking active in editor
- Dark mode: class-based on `<html>`, stored in `localStorage('theme')`, respects `prefers-color-scheme`
- `app/features.py`: feature flags system (`calendar_filters` in beta for superadmin)
- `app/audit.py`: `log_action()` helper — auto-captures IP, UA, and current user from Flask `g`/`request`

## Auth & roles

- `@jwt_required()` / `@admin_required` (admin+superadmin) / `@superadmin_required` / `@optional_auth`
- `@jwt_required` = local wrapper (`app/auth.py:35`), not `flask_jwt_extended`'s directly
- `JWT_TOKEN_LOCATION = ["headers", "cookies"]` — Bearer → no CSRF, cookie-only → CSRF
- Login: JSON body + httpOnly cookie
- Defaults: `admin@valbellunamotorsport.it` / `admin123`, `superadmin@valbellunamotorsport.it` / `superadmin123`
- SuperAdmin hidden from member/participant/report/dashboard queries (`User.ruolo != "superadmin"`)
- Registration tokens DB-backed (`InviteToken` model in `app/models.py`) — persistent across restarts, with configurable expiration

## DB quirks

- `User.attivo` and `Participation.con_macchina` = `Integer(0/1)`, not bool
- `Race.data_inizio`/`data_fine` nullable (`NULL` = no date / single-day)
- `scadenza_conferma` checked vs `datetime.now(UTC).date()` in participation routes
- Calendar view uses `func.strftime("%Y", Race.data_inizio)` — SQLite-only
- Alembic migrations exist (`alembic/versions/`) but `before_request` auto-creates tables → optional
- User emails: `<nome>.lower().replace(" ",".")@valbellunamotorsport.it`

## Templates

- All URLs **hardcoded** (no `url_for`) — match blueprint `url_prefix`
- Forms rendered with WTForms (`app/forms.py`) but POST handlers use `request.get_json()` (not form data)
- Exception: file upload (import backup) uses `FormData` — HTMX can't handle multipart
- `app/static/css/app.css` loaded alongside Tailwind CDN

## JSON error keys

- `/auth` endpoints return `{"detail": "..."}`
- `/races`, `/participation` endpoints return `{"error": "..."}`
- Import route returns `"error"` on failure specifically

## CLI (`python -m app.cli <command>`)

```
list-users                        reset-password <email> [--password]
make-superadmin <email>           make-admin <email>
create-superadmin <email> <nome>  delete-user <email> [-y]
clear-logs
```

## Seed

```bash
python -m app.seed
```

Reads `TEST Calendario 2026 Valbelluna Motorsport.xlsx`. On PythonAnywhere file missing → skip.

## Tests

- `tests/conftest.py` sets `DATABASE_URL=sqlite:///:memory:`, `SECRET_KEY`, `JWT_SECRET` **before** importing app (env var order matters)
- `app` fixture: function-scoped `create_all`/`drop_all`; `db` fixture: `get_db()` session yield
- Token auth: `create_access_token(identity=str(user.id))` → `Authorization: Bearer` header
- Fixtures: `app`, `client`, `db`, `admin_user`, `superadmin_user`, `normal_user`, `*_token`, `auth_headers`

## PythonAnywhere

WSGI: `/var/www/GChiarion_pythonanywhere_com_wsgi.py`
```python
sys.path.insert(0, '/home/GChiarion/ValBellunaMotorsport')
```
Static tab: `/static/` → `/home/GChiarion/ValBellunaMotorsport/app/static/`. Env: `DATABASE_URL`, `JWT_SECRET`, `SECRET_KEY`, `DEBUG=false`. Reload after git pull.
