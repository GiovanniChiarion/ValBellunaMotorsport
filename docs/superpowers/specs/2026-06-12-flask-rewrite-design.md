# ValBelluna Motorsport-Flask: Design Document

## Overview

Rewrite ValBelluna Motorsport from FastAPI to Flask as a **new project** (`ValBelluna Motorsport-Flask/`) alongside the existing FastAPI repo. Goals:
- Deploy on PythonAnywhere free tier ($0, always-on, persistent SQLite)
- Maintain identical functionality (auth, dashboard, admin, reports, history, backup/export/import)
- Preserve all SQLAlchemy models and Jinja2 templates (copied identically, zero changes)
- HTMX + Alpine.js + Tailwind CSS frontend (CDN, unchanged)

## Architecture

### Project structure

```
ValBelluna Motorsport-Flask/
├── app/
│   ├── __init__.py          # app factory: create_app()
│   ├── config.py            # Flask-style config from env vars
│   ├── database.py          # vanilla SQLAlchemy (copied identically)
│   ├── models.py            # 4 models (copied identically)
│   ├── auth.py              # JWT: Flask-JWT-Extended + custom decorators
│   ├── forms.py             # WTForms: Login, Register, Race, Settings
│   ├── seed.py              # Excel seeding (copied identically)
│   ├── cli.py               # Click commands (copied/adapted)
│   ├── tasks.py             # APScheduler (copied identically)
│   ├── templates/           # Jinja2 (copied, minor URL/CSRF adaptations)
│   ├── static/              # static files (copied identically)
│   └── blueprints/
│       ├── __init__.py
│       ├── auth.py          # /auth prefix (12 routes)
│       ├── races.py         # /races prefix (13 routes)
│       ├── participation.py # /participation prefix (4 routes)
│       ├── reports.py       # /reports prefix (1 route)
│       └── history.py       # /history prefix (2 routes)
├── tests/
│   ├── conftest.py          # Flask test client + fixtures
│   ├── test_auth.py
│   ├── test_forms.py
│   ├── test_races.py
│   ├── test_participation.py
│   ├── test_reports.py
│   └── test_history.py
├── alembic/                 # copied identically
├── alembic.ini              # copied, minor path updates
├── requirements.txt
└── .env
```

### Key decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | Flask 3.x | Minimal diff from FastAPI; Jinja2 already shared |
| Auth | Flask-JWT-Extended + JWT in cookies + headers | Same pattern as current app; CSRF-protected |
| Forms | WTForms + Flask-WTF | Server-rendered forms with CSRF; replaces Pydantic |
| ORM | Vanilla SQLAlchemy (no Flask-SQLAlchemy) | Models stay 100% identical; no migration cost |
| Testing | pytest + Flask test client | Same test runner; different client API |

## Auth (Flask-JWT-Extended)

### Configuration

```python
SECRET_KEY = "cambia-questa-chiave"
JWT_SECRET_KEY = "cambia-questa-chiave"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1440)
JWT_TOKEN_LOCATION = ["cookies", "headers"]
JWT_COOKIE_SECURE = False  # True in production
JWT_COOKIE_CSRF_PROTECT = True
JWT_CSRF_IN_COOKIES = True
JWT_COOKIE_SAMESITE = "Lax"
JWT_HEADER_TYPE = "Bearer"
```

### Decorators (in `app/auth.py`)

- `@jwt_required()` → `get_jwt_identity()` → query user by id → store in `g.current_user`
- `@admin_required` → wraps `@jwt_required` + check `g.current_user.ruolo in ("admin", "superadmin")` → `abort(403)`
- `@superadmin_required` → wraps `@jwt_required` + check `g.current_user.ruolo == "superadmin"` → `abort(403)`
- `@optional_auth` → wraps `@jwt_required(optional=True)` → identity may be None → `g.current_user` is User or None

### Guard-to-decorator mapping (matching existing FastAPI guards)

| FastAPI guard | Flask equivalent |
|---|---|
| `Depends(get_current_user)` | `@jwt_required()` + `g.current_user` |
| `Depends(require_admin)` | `@admin_required` |
| `Depends(require_superadmin)` | `@superadmin_required` |
| `Depends(get_optional_user)` | `@optional_auth` (g.current_user may be None) |

### Registration tokens

Current in-memory `set[str]`, lost on restart. Keep same approach: a module-level `registration_tokens: set[str]` in `blueprints/auth.py` (or `app/auth.py`). No change needed.

## Route mapping (FastAPI → Flask)

Each FastAPI router maps to a Flask Blueprint with the same prefix. Decorators change:

```python
# FastAPI:
@router.get("/races", response_class=HTMLResponse)
def calendar_view(request: Request, current_user: User = Depends(get_current_user)):
    ...

# Flask:
@races_bp.route("/races")
@jwt_required()
def calendar_view():
    ...
```

Key differences:
- No `request` parameter — Flask injects `request` globally
- No `response_class` — Flask auto-detects HTML from template rendering
- Guards are decorators, not `Depends()` injections
- URL parameters: `race_id` → `@races_bp.route("/<int:race_id>")` or `request.args.get()` for query params
- Form data: `request.form.get("field")` or WTForms `form.validate_on_submit()`
- JSON: `request.get_json()`

## Forms (WTForms)

```python
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])

class RegisterForm(FlaskForm):
    nome = StringField("Nome", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    token = StringField("Token di registrazione", validators=[DataRequired()])

class RaceForm(FlaskForm):
    descrizione = TextAreaField("Descrizione", validators=[DataRequired()])
    data_inizio = DateField("Data inizio", format="%Y-%m-%d")
    data_fine = DateField("Data fine", format="%Y-%m-%d")
    tipo_gara = SelectField("Tipo gara", coerce=str)
    scadenza_conferma = DateField("Scadenza conferma", format="%Y-%m-%d")
    stato = SelectField("Stato", choices=[
        ("In attesa di conferma", "In attesa di conferma"),
        ("Confermato", "Confermato"),
        ("Annullato", "Annullato"),
    ])
    note_auto = TextAreaField("Note automatiche")

class SelfChangePasswordForm(FlaskForm):
    current_password = PasswordField("Password attuale", validators=[DataRequired()])
    new_password = PasswordField("Nuova password", validators=[DataRequired(), Length(min=6)])
    new_password_confirm = PasswordField("Conferma password", validators=[DataRequired(), EqualTo("new_password")])

class SelfChangeEmailForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    new_email = StringField("Nuova email", validators=[DataRequired(), Email()])

class AdminChangePasswordForm(FlaskForm):
    new_password = PasswordField("Nuova password", validators=[DataRequired(), Length(min=6)])
    new_password_confirm = PasswordField("Conferma password", validators=[DataRequired(), EqualTo("new_password")])

class AdminChangeEmailForm(FlaskForm):
    new_email = StringField("Nuova email", validators=[DataRequired(), Email()])

class RaceTypeForm(FlaskForm):
    codice = StringField("Codice", validators=[DataRequired(), Length(max=20)])
    descrizione = StringField("Descrizione")
```

## Templates adaptation

Templates are **copied verbatim** from the FastAPI project. Changes required:

| Change | Reason |
|--------|--------|
| `{{ url_for("races.calendar_view") }}` etc. | Flask blueprint dot-notation |
| `{{ form.hidden_tag() }}` in login/register/settings | CSRF token for WTForms |
| `current_user` available via context processor | Global in Flask |
| `request` removed from TemplateResponse calls | Flask injects it automatically |
| `flash("Messaggio", "success")` + toast iteration | Replace custom toast JS with Flask flash |
| `{% set current_year = request.args.get("year", "") %}` | `request.args` instead of `request.query_params` |

### Context processor (in `create_app()`)

```python
@app.context_processor
def inject_globals():
    return {
        "current_user": getattr(g, "current_user", None),
        "now": datetime.now(),
    }
```

## Route-by-route implementation order

Implementation follows dependency order (each blueprint depends on auth working first):

1. **auth blueprint** (12 routes): login/logout/register/me/settings/password/email/admin routes
2. **participation blueprint** (4 routes): set_participation, update_nota, toggle_macchina, admin_set
3. **races blueprint** (13 routes): calendar, detail, CRUD, admin dashboard, admin management, export/import
4. **reports blueprint** (1 route): reports page
5. **history blueprint** (2 routes): history view + export

## Seed + CLI + Scheduler

- `app/seed.py` — copied identically (uses SQLAlchemy directly, framework-agnostic)
- `app/cli.py` — reimplemented with Click (`@app.cli.command()` via Flask's built-in Click support)
- `app/tasks.py` — copied identically, registered via `APScheduler` in `create_app()`

## Testing strategy

### Fixtures (conftest.py)

```python
@pytest.fixture
def app():
    app = create_app({"TESTING": True, "DATABASE_URL": "sqlite:///:memory:"})
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        yield app
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def access_token(client):
    """Login as admin, return JWT access token string."""
    login_response = client.post("/auth/login", json={
        "email": "admin@valbellunamotorsport.it",
        "password": "admin123"
    })
    return login_response.get_json()["access_token"]
```

### Auth test approach

Since we're using TDD, each blueprint gets tested first:
1. Write failing test (RED)
2. Implement minimal code (GREEN)
3. Refactor if needed

## Deploy: PythonAnywhere

### Setup steps

```bash
# Clone the new repo
git clone https://github.com/.../ValBelluna Motorsport-Flask.git

# Virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Database
alembic upgrade head
python -m app.seed          # seed from Excel
flask run                   # test locally

# WSGI config (managed by PythonAnywhere web UI)
# Path: /var/www/tuonome_pythonanywhere_com_wsgi.py
# Content: from app import create_app; application = create_app()
```

### Environment variables (set in PythonAnywhere Web tab)

```
SECRET_KEY=<random>
JWT_SECRET_KEY=<random>
DATABASE_URL=sqlite:///home/tuonome/ValBelluna Motorsport-Flask/calendario.db
DEBUG=False
```

### Free tier limits

| Resource | Limit | ValBelluna Motorsport usage |
|----------|-------|---------------------|
| CPU | Throttled at 100% sustained | Well under (CRUD clicks) |
| Storage | 512MB | ~10-20MB |
| Outbound HTTP | Whitelist only | None needed |
| Always-on | Yes | 24/7 |
| Custom domain | No (paid only) | Subdomain `tuonome.pythonanywhere.com` OK |

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| PythonAnywhere outbound HTTP blocked | App doesn't call external APIs |
| SQLite WAL mode may conflict with NFS | Use DELETE journal mode on PA |
| CSRF token mismatch with HTMX requests | Set `JWT_CSRF_METHODS` correctly; test HTMX POSTs |
| Cold start on other platforms | PA has zero cold start |
| Template `url_for` broken | Audit all URL references during template copy |
