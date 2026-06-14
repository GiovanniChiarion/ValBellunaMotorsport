# Token di invito — redesign

## Problema

I token di registrazione sono attualmente gestiti con un `set[str]` in memoria in
`app/blueprints/auth.py:21`, perso a ogni riavvio del server. Inoltre:
- Nessuna scadenza
- Nessuna eliminazione individuale
- Nessuna persistenza / tracciamento
- Bug: `register_page()` non estrae `?token=` dalla query string
- Solo l'ultimo token generato ha pulsante "Copia"
- Descrizioni audit log ridondanti (ripetono `actor_name`)
- Pulsante "Token invito" presente nel calendario (va lasciato solo in admin dashboard)

## Modifiche

### 1. Nuovo modello `InviteToken` (`app/models.py`)

```python
class InviteToken(Base):
    __tablename__ = "invite_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    expires_at = Column(DateTime, nullable=True)  # NULL = mai
    used_at = Column(DateTime, nullable=True)     # NULL = non usato
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    used_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
```

Sostituisce `registration_tokens: set[str]`. Tabella creata automaticamente da
`before_request` → `Base.metadata.create_all`.

### 2. Endpoint modificati (`app/blueprints/auth.py`)

| Endpoint | Metodo | Auth | Cambiamento |
|----------|--------|------|-------------|
| `/auth/register` | GET | — | Legge `?token=` da query string, passa a template; nuovo branch AJAX validate |
| `/auth/register` | POST | — | Query `InviteToken` DB invece di set; marca `used_at` e `used_by_id` |
| `/auth/register/token` | **GET→POST** | admin | Accetta `{"expires_in": "24h"\|"7d"\|"30d"\|"never"}`; crea record DB |
| `/auth/admin/tokens` | GET | admin | Query DB, passa oggetti (id, token, expires_at, used_at, created_at) |

### 3. Nuovi endpoint

| Endpoint | Metodo | Auth | Descrizione |
|----------|--------|------|-------------|
| `/auth/admin/tokens/<id>` | DELETE | admin | Elimina token, log `TOKEN_DELETE` |
| `/auth/admin/tokens/<id>` | PUT | admin | Modifica `expires_at`, log `TOKEN_UPDATE` |
| `/auth/register/token/validate` | GET | — | `?token=xxx` → `{valid: bool}`, per AJAX |

### 4. Login page (`login.html`)

Aggiunto link sotto il form:
```html
<a href="/auth/register" class="...">Registrati con un token</a>
```

### 5. Register page (`register.html`) — due stati

**Stato A — token presente** (da `?token=` in URL o dopo validazione AJAX):
- Token in `<input type="hidden">`
- Form nome, email, password (come ora)
- Submit → POST `/auth/register`

**Stato B — nessun token:**
- Campo per incollare token + bottone "Valida"
- AJAX `GET /auth/register/token/validate?token=xxx`
- Se valido → transizione a Stato A
- Se non valido → errore

### 6. Admin tokens page (`tokens.html`)

**Generazione:** bottone apre select per `expires_in` (24h, 7gg, 30gg, mai), POST
a `/auth/register/token`.

**Lista token attivi:** ogni riga mostra:
- Pallino verde/grigio
- Token troncato
- Badge scadenza
- Bottone "Copia link"
- Bottone "Modifica scadenza"
- Bottone "Elimina" (conferma JS, DELETE)

### 7. Rimuovi pulsante da calendario

In `dashboard.html` (righe 96-99), rimuovere il link "Token invito".
Resta in `admin/dashboard.html` e `admin/members.html`.

### 8. Audit log — descrizioni non ridondanti

- `"Token generato da {admin}"` → `"Token generato"`
- `"Password cambiata da {admin} per {target}"` → `"Password cambiata per {target}"`
- `"Email cambiata da {admin} per {target}: ..."` → `"Email cambiata per {target}: ..."`

### 9. Test

- `test_auth.py`: crea `InviteToken` nel DB invece di `registration_tokens.add()`
- `test_auth.py`: GET → POST per generazione token; nuovi test per DELETE/PUT
- `test_auth_audit.py`: adattato a DB

### 10. Files modificati

```
app/models.py              + InviteToken model
app/blueprints/auth.py     - in-memory set, + DB queries, nuovi endpoint, fix register GET
app/templates/login.html   + link registrazione
app/templates/register.html  due stati, AJAX validate
app/templates/admin/tokens.html  select durata, per-token copy/edit/delete
app/templates/dashboard.html  - pulsante token invito
tests/test_auth.py         test aggiornati
tests/test_auth_audit.py   test aggiornati
```

### 11. Non incluso

- Nessuna migrazione Alembic (auto-create tabelle)
- Nessun feature flag
- Nessuna notifica alla scadenza
