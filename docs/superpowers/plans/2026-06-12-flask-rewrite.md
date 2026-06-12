# CalendarioKart-Flask Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite CalendarioKart from FastAPI to Flask as a new project deployable on PythonAnywhere free tier.

**Architecture:** Flask 3.x app factory pattern, vanilla SQLAlchemy (models identical to FastAPI), Flask-JWT-Extended for auth, WTForms for server-rendered forms, Jinja2 templates (copied verbatim with minor adaptations).

**Tech Stack:** Flask 3, Flask-JWT-Extended, Flask-WTF/WTForms, SQLAlchemy 2.0, bcrypt, Jinja2, pytest

---

### Task 1: Project skeleton + config + database + models

**Files:**
- Create: `CalendarioKart-Flask/requirements.txt`
- Create: `CalendarioKart-Flask/.env`
- Create: `CalendarioKart-Flask/app/__init__.py`
- Create: `CalendarioKart-Flask/app/config.py`
- Create: `CalendarioKart-Flask/app/database.py` (copied from FastAPI)
- Create: `CalendarioKart-Flask/app/models.py` (copied from FastAPI)

- [ ] **Step 1: Create project directory**

Run:
```bash
mkdir -p /home/giovanni/Documents/CalendarioKart-Flask/app/blueprints
mkdir -p /home/giovanni/Documents/CalendarioKart-Flask/app/templates
mkdir -p /home/giovanni/Documents/CalendarioKart-Flask/app/templates/admin
mkdir -p /home/giovanni/Documents/CalendarioKart-Flask/app/static
mkdir -p /home/giovanni/Documents/CalendarioKart-Flask/tests
```

- [ ] **Step 2: Write requirements.txt**

```txt
flask>=3.1.0
flask-jwt-extended>=4.7.0
flask-wtf>=1.2.0
wtforms>=3.2.0
sqlalchemy>=2.0.36
alembic>=1.14.0
bcrypt==4.1.3
python-multipart>=0.0.12
jinja2>=3.1.4
openpyxl>=3.1.5
apscheduler>=3.10.4
python-dateutil>=2.9.0
pydantic-settings>=2.7.0
pytest>=8.0.0
```

- [ ] **Step 3: Write app/config.py**

```python
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./calendario.db"
    jwt_secret: str = "cambia-questa-chiave-in-produzione"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    app_name: str = "CalendarioKart"
    app_version: str = "1.0.0"
    debug: bool = False
    secret_key: str = "cambia-questa-chiave-in-produzione"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Copy database.py from FastAPI project**

- [ ] **Step 5: Copy models.py from FastAPI project**

- [ ] **Step 6: Write .env**

```
DATABASE_URL="sqlite:///./calendario.db"
DEBUG=true
SECRET_KEY="dev-secret-key"
JWT_SECRET="dev-jwt-secret"
```

- [ ] **Step 7: Write app/__init__.py (app factory skeleton)**

```python
from flask import Flask
from app.config import get_settings


def create_app(test_config=None) -> Flask:
    app = Flask(__name__)
    settings = get_settings()

    app.config["SECRET_KEY"] = settings.secret_key
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 1440 * 60
    app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
    app.config["JWT_COOKIE_SECURE"] = not settings.debug
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_CSRF_IN_COOKIES"] = True
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    app.config["JWT_HEADER_TYPE"] = "Bearer"

    if test_config:
        app.config.update(test_config)

    return app
```

### Task 2: Auth (Flask-JWT-Extended + decorators)

**Files:**
- Create: `CalendarioKart-Flask/app/auth.py`

Write test first, then implement.

### Task 3: Forms (WTForms)

**Files:**
- Create: `CalendarioKart-Flask/app/forms.py`

Write test first, then implement.

### Task 4: Auth blueprint

**Files:**
- Create: `CalendarioKart-Flask/app/blueprints/__init__.py`
- Create: `CalendarioKart-Flask/app/blueprints/auth.py`

Write test first, then implement. 12 routes: login GET/POST, logout, register GET/POST, registration token gen, me, settings, change password/email (self + admin), admin tokens.

### Task 5: Participation blueprint

**Files:**
- Create: `CalendarioKart-Flask/app/blueprints/participation.py`

Write test first, then implement. 4 routes: set_participation, update_nota, toggle_macchina, admin_set.

### Task 6: Races blueprint

**Files:**
- Create: `CalendarioKart-Flask/app/blueprints/races.py`

Write test first, then implement. 13 routes: calendar, detail, CRUD, admin dashboard, admin members, race types, export/import.

### Task 7: Reports + History blueprints

**Files:**
- Create: `CalendarioKart-Flask/app/blueprints/reports.py`
- Create: `CalendarioKart-Flask/app/blueprints/history.py`

Write test first, then implement. 1 report route + 2 history routes.

### Task 8: App factory completion + CLI + Templates

**Files:**
- Modify: `CalendarioKart-Flask/app/__init__.py` (register blueprints, context processor, seed admin)
- Create: `CalendarioKart-Flask/app/cli.py`
- Copy: templates + static from FastAPI
- Copy: `app/seed.py` from FastAPI
- Copy: `app/tasks.py` from FastAPI

### Task 9: Copy Alembic

Copy alembic/ directory and alembic.ini from FastAPI project.

### Task 10: Write full test suite

Cover all blueprints with integration tests.

### Task 11: Full verification

```bash
pip install -r requirements.txt
alembic upgrade head
python -m pytest tests/ -v
ruff check app/ tests/
```
