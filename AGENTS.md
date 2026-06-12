# CalendarioKart (Flask)

Kart association calendar: Flask rewrite of the original FastAPI project.

## Stack

Python 3.14 + Flask 3.1 + Flask-JWT-Extended + SQLAlchemy 2.0 + Alembic + bcrypt + Jinja2 + HTMX + Alpine.js + Tailwind CSS (CDN).

## Startup

```bash
# Quick start (one click — double-click start.sh in file manager)
./start.sh

# Or manually:
.venv/bin/python run.py
# → http://localhost:8000
```

## Commands

```bash
.venv/bin/ruff check app/ tests/          # lint
.venv/bin/ruff format --check app/ tests/ # format check
.venv/bin/pyright                           # type check
.venv/bin/python -m pytest tests/ -v       # test suite (50 tests)
.venv/bin/python -m app.seed               # seed DB from xlsx
.venv/bin/python -m app.cli list-users     # CLI admin: lista utenti
.venv/bin/python -m app.cli reset-password <email>
.venv/bin/python -m app.cli make-superadmin <email>
.venv/bin/python -m app.cli make-admin <email>
.venv/bin/python -m app.cli create-superadmin <email> <nome>
.venv/bin/python -m app.cli delete-user <email>
```

**Order**: lint → format → pyright → test.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed
```

Default admin: `admin@calendariokart.it` / `admin123`. SuperAdmin: `superadmin@calendariokart.it` / `superadmin123`.

## Key differences from FastAPI version

- **App factory**: `app/__init__.py` has `create_app()` instead of global app instance.
- **Auth**: Flask-JWT-Extended instead of python-jose. JWT in cookies + `Authorization: Bearer` header. `@jwt_required()` / `@admin_required` / `@superadmin_required` / `@optional_auth` decorators from `app.auth`.
- **Database**: Vanilla SQLAlchemy with `get_db()` context manager. WAL → DELETE journal mode for PythonAnywhere.
- **Forms**: WTForms defined in `app/forms.py` but templates use raw HTML + JS fetch (identical to FastAPI).
- **Routes**: All routes are on blueprints with `url_prefix`: `/auth`, `/races`, `/participation`, `/reports`, `/history`.
- **Entry**: `run.py` creates the app; `start.sh` for one-click launch.

## Deploy (PythonAnywhere)

1. Upload project to PythonAnywhere (git clone or direct upload).
2. Set up virtualenv with `requirements.txt`.
3. In PythonAnywhere Web tab, set WSGI file to:
   ```python
   import sys
   sys.path.insert(0, '/home/youruser/CalendarioKart-Flask')
   from app import create_app
   application = create_app()
   ```
4. Set env vars (or keep `.env` file) for `DATABASE_URL`, `SECRET_KEY`, `JWT_SECRET`.
5. Run `alembic upgrade head` and `python -m app.seed` in a Bash console.
