# Role Impersonation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow SuperAdmin to toggle between "superadmin", "admin", and "membro" roles without logging out.

**Architecture:** Flask session stores `impersonated_role`; `g.effective_role` is computed in auth callbacks; decorators and templates check `g.effective_role` instead of `g.current_user.ruolo`.

**Tech Stack:** Flask session, Flask-JWT-Extended, Alpine.js, HTMX

---

### Task 1: `g.effective_role` in auth callbacks

**Files:**
- Modify: `app/auth.py:18-24` (user_lookup_callback)
- Modify: `app/auth.py:66-84` (optional_auth)
- Modify: `app/blueprints/history.py:21` (ACTION_TYPES)

- [ ] **Add `session` import to auth.py**

In `app/auth.py`, add `from flask import session` alongside existing `from flask import abort, g`:

```python
from flask import abort, g, session
```

- [ ] **Set `g.effective_role` in `user_lookup_callback`**

After `g.current_user = user` at line 23, add:

```python
g.effective_role = (
    session.get("impersonated_role") or user.ruolo
) if user else None
```

- [ ] **Set `g.effective_role` in `optional_auth`**

After `g.current_user = user` at line 77, add:

```python
g.effective_role = (
    session.get("impersonated_role") or user.ruolo
) if user else None
```

After `g.current_user = None` at line 80, add:

```python
g.effective_role = None
```

- [ ] **Add `"IMPERSONATE"` to `ACTION_TYPES` in history.py**

```python
ACTION_TYPES = [
    "LOGIN", "LOGOUT", "LOGIN_FAILED",
    "CREATE", "UPDATE", "DELETE",
    "VIEW", "EXPORT", "IMPORT",
    "REGISTER", "PASSWORD_CHANGE", "EMAIL_CHANGE",
    "TOKEN_GENERATE", "ROLE_CHANGE", "USER_TOGGLE",
    "IMPERSONATE",
]
```

---

### Task 2: Modify decorators to use `g.effective_role`

**Files:**
- Modify: `app/auth.py:44-52` (admin_required)
- Modify: `app/auth.py:55-62` (superadmin_required)
- Modify: `app/blueprints/races.py:100` (inline check)

- [ ] **Change `@admin_required` to use `g.effective_role`**

```python
def admin_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        if g.effective_role not in ("admin", "superadmin"):
            abort(403)
        return fn(*args, **kwargs)
    return wrapper
```

- [ ] **Change `@superadmin_required` to use `g.effective_role`**

```python
def superadmin_required(fn):
    @wraps(fn)
    @_jwt_required()
    def wrapper(*args, **kwargs):
        if g.effective_role != "superadmin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper
```

- [ ] **Change inline check in `race_detail` (races.py:100)**

```python
is_admin = g.effective_role in ("admin", "superadmin")
```

---

### Task 3: Add `POST /auth/impersonate` endpoint + context processor

**Files:**
- Modify: `app/blueprints/auth.py` (new route)
- Modify: `app/__init__.py:44-48` (context processor)
- Modify: `app/__init__.py` (before_request fallback)

- [ ] **Add `POST /auth/impersonate` endpoint**

In `app/blueprints/auth.py`, add before `def validate_registration_token`:

```python
@auth_bp.route("/impersonate", methods=["POST"])
@superadmin_required
def impersonate():
    data = request.get_json(silent=True) or {}
    ruolo = data.get("ruolo")
    if ruolo is not None and ruolo not in ("admin", "membro"):
        return jsonify({"detail": "Ruolo non valido"}), 400

    old = session.get("impersonated_role") or "superadmin"
    if ruolo is None:
        session.pop("impersonated_role", None)
    else:
        session["impersonated_role"] = ruolo
    new = session.get("impersonated_role") or "superadmin"

    g.effective_role = new

    with get_db() as db:
        log_action(
            db=db,
            action="IMPERSONATE",
            entity_type="auth",
            description=f"Impersonazione: {g.current_user.nome}: {old} → {new}",
        )
        db.commit()

    return jsonify({"effective_role": new})
```

- [ ] **Add `effective_role` to context processor in `__init__.py`**

```python
@app.context_processor
def inject_globals():
    effective_role = getattr(g, "effective_role", None)
    if effective_role is None and getattr(g, "current_user", None):
        effective_role = g.current_user.ruolo
    return {
        "current_user": getattr(g, "current_user", None),
        "effective_role": effective_role,
        "now": datetime.now(UTC),
    }
```

- [ ] **Add `before_request` fallback for `g.effective_role`**

After `log_page_view`, add a third `before_request`:

```python
@app.before_request
def ensure_effective_role():
    if "effective_role" not in g:
        g.effective_role = None
```

---

### Task 4: Template changes

**Files:**
- Modify: `app/templates/base.html` (navbar)
- Modify: `app/templates/settings.html` (badge)

- [ ] **Replace `current_user.ruolo` → `effective_role` in base.html**

All instances where `current_user.ruolo` is used for permission checks:

| Line(s) | Change |
|---------|--------|
| 62 | `current_user.ruolo in ('admin', 'superadmin')` → `effective_role in ('admin', 'superadmin')` |
| 75 | `current_user.ruolo == 'superadmin'` → `effective_role == 'superadmin'` |
| 99 | `current_user.ruolo == 'superadmin'` → `effective_role == 'superadmin'` |
| 101 | `current_user.ruolo == 'admin'` → `effective_role == 'admin'` |
| 129 | `current_user.ruolo in ('admin', 'superadmin')` → `effective_role in ('admin', 'superadmin')` |
| 139 | `current_user.ruolo == 'superadmin'` → `effective_role == 'superadmin'` |
| 149 | `current_user.ruolo == 'superadmin'` → `effective_role == 'superadmin'` |
| 151 | `current_user.ruolo == 'admin'` → `effective_role == 'admin'` |

- [ ] **Add Alpine dropdown toggle in navbar**

After the role badge span (around line 103), add impersonation dropdown (only for superadmin):

```html
{% if current_user.ruolo == 'superadmin' %}
<div class="relative ml-1" x-data="{ open: false }">
    <button @click="open = !open" class="flex items-center space-x-0.5 text-[10px] font-bold bg-violet-500 text-white px-1.5 py-0.5 rounded-full hover:bg-violet-600 transition-colors">
        <span>{{ effective_role }}</span>
        <svg class="size-3" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd"/></svg>
    </button>
    <div x-show="open" @click.outside="open = false" x-transition.duration.100ms
         class="absolute right-0 mt-1 w-40 bg-white dark:bg-slate-700 rounded-xl shadow-lg border border-gray-200 dark:border-slate-600 py-1 z-50">
        <button @click="fetch('/auth/impersonate', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+localStorage.getItem('token')}, body:JSON.stringify({ruolo:null})}).then(r=>location.reload())"
                class="w-full text-left px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-600 flex items-center space-x-2"
                :class="{'bg-violet-100 dark:bg-violet-900/30': '{{ effective_role }}' == 'superadmin'}">
            <span x-show="'{{ effective_role }}' == 'superadmin'">●</span>
            <span x-show="'{{ effective_role }}' != 'superadmin'">○</span>
            <span>SuperAdmin</span>
        </button>
        <button @click="fetch('/auth/impersonate', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+localStorage.getItem('token')}, body:JSON.stringify({ruolo:'admin'})}).then(r=>location.reload())"
                class="w-full text-left px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-600 flex items-center space-x-2"
                :class="{'bg-violet-100 dark:bg-violet-900/30': '{{ effective_role }}' == 'admin'}">
            <span x-show="'{{ effective_role }}' == 'admin'">●</span>
            <span x-show="'{{ effective_role }}' != 'admin'">○</span>
            <span>Admin</span>
        </button>
        <button @click="fetch('/auth/impersonate', {method:'POST', headers:{'Content-Type':'application/json','Authorization':'Bearer '+localStorage.getItem('token')}, body:JSON.stringify({ruolo:'membro'})}).then(r=>location.reload())"
                class="w-full text-left px-3 py-1.5 text-xs font-medium text-gray-700 dark:text-slate-200 hover:bg-gray-100 dark:hover:bg-slate-600 flex items-center space-x-2"
                :class="{'bg-violet-100 dark:bg-violet-900/30': '{{ effective_role }}' == 'membro'}">
            <span x-show="'{{ effective_role }}' == 'membro'">●</span>
            <span x-show="'{{ effective_role }}' != 'membro'">○</span>
            <span>Utente</span>
        </button>
    </div>
</div>
{% endif %}
```

- [ ] **Replace `current_user.ruolo` → `effective_role` in settings.html**

Lines 23-27:

```html
{% if effective_role == 'superadmin' %}
<span class="text-[10px] font-bold bg-violet-500 text-white px-1.5 py-0.5 rounded-full">superadmin</span>
{% elif effective_role == 'admin' %}
<span class="text-[10px] font-bold bg-yellow-400 text-yellow-900 px-1.5 py-0.5 rounded-full">admin</span>
{% endif %}
```

---

### Task 5: Write tests

**Files:**
- Create: `tests/test_impersonation.py`

- [ ] **Write tests for impersonation**

```python
from flask import session


def test_impersonate_not_available_for_admin(client, admin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 403


def test_impersonate_not_available_for_user(client, user_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_superadmin_impersonate_admin(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "admin"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["effective_role"] == "admin"


def test_superadmin_impersonate_membro(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["effective_role"] == "membro"


def test_superadmin_revert_impersonation(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["effective_role"] == "membro"

    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": None},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["effective_role"] == "superadmin"


def test_invalid_role_rejected(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "invalid"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 400


def test_impersonated_membro_cannot_access_admin(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/races/admin/dashboard",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 403


def test_impersonated_admin_cannot_access_superadmin(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "admin"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/history",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 403


def test_impersonated_admin_can_access_admin_routes(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "admin"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/races/admin/dashboard",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200


def test_reverted_superadmin_regains_access(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": None},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/history",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
```

---

### Task 6: Verify

- [ ] **Run linter and type checker**

```bash
.venv/bin/ruff check app/ tests/
.venv/bin/ruff format --check app/ tests/
.venv/bin/pyright
```

- [ ] **Run tests**

```bash
.venv/bin/python -m pytest tests/ -v
```

- [ ] **Run new impersonation tests specifically**

```bash
.venv/bin/python -m pytest tests/test_impersonation.py -v
```
