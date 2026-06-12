# Rewrite Log: FastAPI → Flask

**Data**: 2026-06-12
**Progetto originale**: `CalendarioKart/` (FastAPI, Fly.io)
**Nuovo progetto**: `CalendarioKart-Flask/` (Flask, PythonAnywhere)

## Perché il rewrite

- FastAPI è overkill per un'app CRUD server-rendered con HTMX
- PythonAnywhere free tier non supporta nativamente ASGI
- Flask è più leggero e lineare per template Jinja2 + HTMX + form
- Nessun bisogno di async, WebSocket, o API pubbliche

## Decisioni architetturali

### 1. Flask invece di FastAPI

| Aspetto | Scelta | Motivazione |
|---------|--------|-------------|
| Framework | Flask 3.1.3 | PythonAnywhere native WSGI |
| Auth | Flask-JWT-Extended (cookies + headers) | Stesso pattern FastAPI, CSRF via double-submit cookie |
| Form | WTForms con Flask-WTF | Validazione lato server integrata |
| DB | Vanilla SQLAlchemy 2.0 | Modelli copiati identici, zero migrazioni |
| ORM | `sessionmaker` + context manager | Stessa API del progetto originale |

### 2. JWT_TOKEN_LOCATION: headers prima di cookies

**Decisione**: `JWT_TOKEN_LOCATION = ["headers", "cookies"]`

**Perché**: Le richieste con `Authorization: Bearer` (fetch JS, HTMX) devono bypassare il CSRF check. Solo le richieste cookie-only (form HTML nativi) richiedono CSRF. Con cookies prima di headers, tutte le richieste passano dal CSRF check fallendo quelle via Bearer.

**Effetto**: Template admin con HTMX richiedono header `Authorization: Bearer` invece di affidarsi al cookie.

### 3. WAL → DELETE journal mode

**Decisione**: `journal_mode=DELETE` invece di WAL

**Perché**: PythonAnywhere usa NFS che non supporta WAL mode. DELETE è l'unica modalità compatibile.

### 4. File upload import: fetch() invece di HTMX

**Decisione**: Form di import backup usa JavaScript nativo (`fetch()` + `FormData`) invece di HTMX `hx-post`

**Perché**: HTMX non gestisce correttamente file upload multipart con `hx-trigger="change"` su input figli. Il server si aspetta `request.files['file']` e risponde con JSON.

**Pattern**:
```javascript
var fd = new FormData(this.closest('form'));
var t = localStorage.getItem('token');
fetch('/races/admin/import', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer ' + t },
  body: fd
})
```

### 5. Chiavi errore: `"error"` vs `"detail"`

**Decisione**: La route di import (`import_all_data`) usa chiave `"error"` nelle risposte JSON. Tutte le altre route usano `"detail"`.

**Motivazione**: La route di import restituiva già `"error"` nel progetto FastAPI. Le route di auth usano `"detail"` per compatibilità coi template.

### 6. Vanilla SQLAlchemy (no Flask-SQLAlchemy)

**Decisione**: Usare `sessionmaker` diretto invece di `flask-sqlalchemy`

**Perché**: I modelli sono identici al progetto FastAPI. Flask-SQLAlchemy richiederebbe di ereditare da `db.Model` invece di `declarative_base()`.

### 7. In-memory registration tokens

**Decisione**: `registration_tokens: set[str]` in-memory in `blueprints/auth.py` — persi al riavvio

**Perché**: Identico al comportamento FastAPI. Su PythonAnywhere il riavvio è raro e controllato.

### 8. JWT key length (dev vs production)

**Decisione**: In `.env` di sviluppo si usano chiavi corte (15-16 byte) che generano `InsecureKeyLengthWarning`

**Perché**: In produzione su PythonAnywhere, `.env` o `os.environ` conterrà una chiave ≥ 32 byte generata con `openssl rand -hex 32`.

### 9. App factory pattern

**Decisione**: `app/__init__.py` è una funzione `create_app()` chiamata da `run.py` e dai test

**Perché**: Pattern standard Flask; permette configurazione diversa per test (DB in-memory, SECRET_KEY fisso).

### 10. DB init on first request

**Decisione**: `@app.before_request` esegue `Base.metadata.create_all` + crea admin/superadmin default se assenti

**Perché**: Nessun passo di init separato; funziona subito dopo `pip install -r requirements.txt`.

## Cronologia modifiche

1. Creazione scheletro progetto, venv, dipendenze
2. Copia identica: `database.py`, `models.py`, `seed.py`, `tasks.py`, `alembic/`, template/, static/
3. `app/config.py`: pydantic-settings con DATABASE_URL, JWT_SECRET, SECRET_KEY, DEBUG
4. `app/auth.py`: JWTManager, hash_password, decorators (jwt_required, admin_required, superadmin_required, optional_auth)
5. `app/database.py`: vanilla SQLAlchemy con context manager + DELETE journal
6. `app/forms.py`: 8 WTForms (Login, Register, Race, SelfChangePassword, SelfChangeEmail, AdminChangePassword, AdminChangeEmail, RaceTypeForm)
7. `app/__init__.py`: app factory, blueprint registration, JWT config, context processor, before_request DB init
8. `app/cli.py`: 6 Click commands per user management
9. 50 test su 5 file — tutti passanti
10. Fix auth blueprint: error keys "error" → "detail"
11. Fix `JWT_TOKEN_LOCATION`: ["headers", "cookies"] invece di ["cookies", "headers"]
12. Import form: HTMX → fetch() per file upload
13. Copia documentazione e generazione questo log
14. Archivio FastAPI con tag `fastapi-archive`

## Modifiche ai template

| File | Modifica |
|------|----------|
| `base.html` | Aggiunta `handleImportResponse()` JS + `htmx:afterRequest` listener (poi non usato) |
| `dashboard.html` | Form import: HTMX → fetch() + Authorization: Bearer |
| `admin/dashboard.html` | Form import: HTMX → fetch() + Authorization: Bearer |
| Tutti | `url_for` assenti — tutti URL hardcoded (match blueprint url_prefix) |

## Progetto FastAPI originale

- Repo: `/home/giovanni/Documents/CalendarioKart/`
- Deploy: Fly.io (`fly.toml`, `Dockerfile`)
- Archivato con tag git: `fastapi-archive`
- GitHub: repo privato
