# Role Impersonation for SuperAdmin

**Date:** 2026-06-14

## Problem

SuperAdmin needs to test functionality as Admin or normal User without logging out. Currently they must logout/login to switch roles.

## Solution

Add a role-impersonation toggle in the navbar (visible only to superadmin) that overrides `g.effective_role` for permission checks. The underlying DB role is never changed.

## Architecture

### Backend

**`POST /auth/impersonate`** — new endpoint, `@superadmin_required`
- Accepts `{ "ruolo": "admin" | "membro" | null }` in JSON body
- `null` → clears impersonation (reverts to superadmin)
- Stores/clears `session["impersonated_role"]`
- Logs the action via `log_action` with `action="IMPERSONATE"`
- Returns `{ "effective_role": <current effective role> }`

**`g.effective_role`** — set in multiple places to cover all auth paths:
- `user_lookup_callback` (JWT routes): after setting `g.current_user`, compute `g.effective_role = session.get("impersonated_role") or user.ruolo`
- `optional_auth` decorator: after setting `g.current_user`, compute `g.effective_role` same way; else `g.effective_role = None`
- `before_request` fallback: `g.effective_role = getattr(g, "effective_role", None)` to ensure it's always defined

**Decorator changes** (`app/auth.py`):

| Decorator | Current check | New check |
|-----------|--------------|-----------|
| `@admin_required` | `g.current_user.ruolo in ("admin", "superadmin")` | `g.effective_role in ("admin", "superadmin")` |
| `@superadmin_required` | `g.current_user.ruolo == "superadmin"` | `g.effective_role == "superadmin"` |

**Inline check** (`app/blueprints/races.py:100`):
- `is_admin = g.current_user.ruolo in ("admin", "superadmin")` → `g.effective_role in ("admin", "superadmin")`

**Template context** (`app/__init__.py:44-48`):
- Add `effective_role` alongside `current_user`

**No changes:**
- JWT creation/storage — token identity unchanged
- User model — no new columns
- DB queries filtering `User.ruolo != "superadmin"` — correct, superadmin stays hidden from member lists

### Frontend

**Navbar toggle** (`app/templates/base.html`):

Alpine.js dropdown next to the role badge. Only rendered when `effective_role` or `current_user.ruolo == "superadmin"`.

```
[badge: superadmin] ▼
├─ ● SuperAdmin     ← current effective_role
├─ ○ Admin          → POST /auth/impersonate { ruolo: "admin" }
└─ ○ Utente         → POST /auth/impersonate { ruolo: "membro" }
```

When impersonating: badge shows `superadmin → admin` with a red X button to revert (POST `{ ruolo: null }`).

**Nav link visibility** — all template `if current_user.ruolo in/==` checks switch to `effective_role`:
- Calendario — always visible (authenticated)
- Dashboard — `effective_role in ("admin", "superadmin")`
- Membri — `effective_role in ("admin", "superadmin")`
- Report — `effective_role in ("admin", "superadmin")`
- Storico — `effective_role == "superadmin"`
- Role badge — shows badge for `effective_role`

### Audit

- `log_action(action="IMPERSONATE", ...)` on every toggle
- Fields: `old_value` = previous effective_role, `new_value` = new effective_role
- Added to `ACTION_TYPES` in `history.py`

## Files changed

| File | Change |
|------|--------|
| `app/auth.py` | Modify `@admin_required`, `@superadmin_required` to use `g.effective_role`; add `set_effective_role()` helper |
| `app/__init__.py` | Add `before_request` to compute `g.effective_role`; add `effective_role` to context processor |
| `app/blueprints/auth.py` | Add `POST /auth/impersonate` endpoint |
| `app/blueprints/races.py` | Update inline role check in `race_detail` |
| `app/blueprints/history.py` | Add `"IMPERSONATE"` to `ACTION_TYPES` |
| `app/templates/base.html` | Replace `current_user.ruolo` → `effective_role` in nav; add Alpine dropdown toggle |
| `app/templates/settings.html` | Update `current_user.ruolo` → `effective_role` for badge |

## Testing

- SuperAdmin impersonating Admin: can access admin routes (dashboard, members), cannot access superadmin-only routes (history)
- SuperAdmin impersonating User: cannot access any admin routes, cannot see admin nav links
- SuperAdmin reverting: full powers restored
- Nav reflects impersonated role (badge, link visibility)
- Normal Admin/User cannot access impersonation endpoint
- Session cleared on logout → role reverts automatically
