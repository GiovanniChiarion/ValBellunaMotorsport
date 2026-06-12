# CalendarioKart

Kart association calendar app — Flask 3.1, SQLAlchemy 2.0, Flask-JWT-Extended, Jinja2 + HTMX + Alpine.js + Tailwind CSS (CDN). Deployed on PythonAnywhere.

## Quick start

```bash
./start.sh                    # one-click
.venv/bin/python run.py       # → http://localhost:8000
```

## Verification pipeline (run in order)

```bash
.venv/bin/ruff check app/ tests/
.venv/bin/ruff format --check app/ tests/
.venv/bin/pyright
.venv/bin/python -m pytest tests/ -v
```

## Blueprints & routes

| Blueprint | Prefix | Routes | Notable |
|-----------|--------|--------|---------|
| `auth` | `/auth` | 14 (login, register, settings, tokens, admin change credentials) | Registration tokens in-memory → lost on restart. Change-email/password via JS fetch + JSON |
| `races` | `/races` | 18 (calendar, detail, CRUD, admin dashboard, members, types, export/import) | Export/import guarded by `@superadmin_required`. Import route returns `"error"` key (not `"detail"`) on failure |
| `participation` | `/participation` | 4 (set status, note, macchina toggle, admin override) | Admin override bypasses `scadenza_conferma`. All routes log to AuditLog |
| `reports` | `/reports` | 1 (aggregate stats) | Admin-only. Filters out `ruolo == "superadmin"` |
| `history` | `/history` | 2 (last 200 logs, export JSON) | Export is superadmin-only, no row limit |

## CLI (`python -m app.cli <command>`)

```
list-users                        reset-password <email>
make-superadmin <email>           make-admin <email>
create-superadmin <email> <nome>  delete-user <email>
```

## Auth & roles

- `@jwt_required()` / `@admin_required` (admin+superadmin) / `@superadmin_required` / `@optional_auth` (home page, sets `g.current_user=None` on no token)
- JWT in both cookies and `Authorization: Bearer` header. Token location config: `["headers", "cookies"]` — Bearer requests skip CSRF, cookie-only requests require CSRF. Login sets JSON + httpOnly cookie.
- Defaults: `admin@calendariokart.it` / `admin123`, `superadmin@calendariokart.it` / `superadmin123`
- SuperAdmin hidden from member lists, participant lists, reports, dashboards (`User.ruolo != "superadmin"` in queries)

## Database

- **Vanilla SQLAlchemy** (not Flask-SQLAlchemy): `Base`, `engine`, `SessionLocal`, `get_db()` context manager in `app/database.py`
- **DELETE journal mode** (not WAL) — PythonAnywhere NFS compatibility
- `User.attivo` and `Participation.con_macchina` are `Integer` (0/1), not bool
- `Race.data_fine` is nullable (`NULL` for single-day races)
- `before_request` auto-creates tables + default admin/superadmin on first request

## Tests

- `conftest.py` sets `DATABASE_URL=sqlite:///:memory:`, `SECRET_KEY=test-secret-key`, `JWT_SECRET=test-jwt-secret` **before** importing app
- Fixtures: `app` (session-scoped create_all/drop_all), `client`, `db`, `*_user`, `*_token`, `auth_headers`
- Token auth: `create_access_token(identity=str(user.id))` → pass as `Authorization: Bearer` header

## PythonAnywhere deploy

```bash
# On PythonAnywhere Bash console:
git clone git@github.com:GiovanniChiarion/KartProject.git
mkvirtualenv --python=python3.13 kart
pip install -r requirements.txt
# After local changes: git pull + pip install -r requirements.txt (if deps changed)
```

WSGI file (`/var/www/GChiarion_pythonanywhere_com_wsgi.py`):

```python
import sys, os
sys.path.insert(0, '/home/GChiarion/KartProject')
os.environ['DATABASE_URL'] = 'sqlite://///home/GChiarion/KartProject/calendario.db'
os.environ['JWT_SECRET'] = '<openssl rand -hex 32>'
os.environ['SECRET_KEY'] = '<openssl rand -hex 32>'
os.environ['DEBUG'] = 'false'
from app import create_app
application = create_app()
```

Static files Web tab: `/static/` → `/home/GChiarion/KartProject/app/static/`. Reload after every `git pull`.

## Seed

`python -m app.seed` reads `TEST Calendario 2026 Valbelluna Motorsport.xlsx` for bulk import. On PythonAnywhere the file doesn't exist → skips gracefully (admin/superadmin/race types already created by `before_request`).
