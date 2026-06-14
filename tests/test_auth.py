def test_login_page_get(client):
    resp = client.get("/auth/login")
    assert resp.status_code == 200
    assert b"Login" in resp.data or b"login" in resp.data


def test_login_success(client):
    from app.auth import hash_password
    from app.database import get_db
    from app.models import User

    with get_db() as db:
        user = User(
            nome="Test",
            email="login@test.com",
            password_hash=hash_password("pass123"),
            ruolo="membro",
            attivo=1,
        )
        db.add(user)
        db.commit()

    resp = client.post(
        "/auth/login",
        json={
            "email": "login@test.com",
            "password": "pass123",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data


def test_login_invalid_password(client):
    from app.auth import hash_password
    from app.database import get_db
    from app.models import User

    with get_db() as db:
        user = User(
            nome="Test",
            email="login2@test.com",
            password_hash=hash_password("pass123"),
            ruolo="membro",
            attivo=1,
        )
        db.add(user)
        db.commit()

    resp = client.post(
        "/auth/login",
        json={
            "email": "login2@test.com",
            "password": "wrongpass",
        },
    )
    assert resp.status_code == 401


def test_login_invalid_email(client):
    resp = client.post(
        "/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "pass123",
        },
    )
    assert resp.status_code == 401


def test_register_page_get(client):
    resp = client.get("/auth/register")
    assert resp.status_code == 200


def test_register_success(client, admin_user):
    from app.database import get_db
    from app.models import InviteToken

    with get_db() as db:
        t = InviteToken(token="valid-token-db", created_by_id=admin_user.id)
        db.add(t)
        db.commit()

    resp = client.post(
        "/auth/register",
        json={
            "nome": "New User",
            "email": "new@test.com",
            "password": "newpass123",
            "token": "valid-token-db",
        },
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data


def test_register_invalid_token(client):
    resp = client.post(
        "/auth/register",
        json={
            "nome": "New User",
            "email": "new2@test.com",
            "password": "newpass123",
            "token": "invalid-token",
        },
    )
    assert resp.status_code == 400


def test_logout(client):
    resp = client.post("/auth/logout")
    assert resp.status_code == 200


def test_get_me_authenticated(client, admin_token):
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "nome" in data
    assert "email" in data
    assert "ruolo" in data


def test_get_me_unauthenticated(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_settings_page(client, auth_headers):
    resp = client.get("/auth/settings", headers=auth_headers)
    assert resp.status_code == 200


def test_change_own_password(client, auth_headers, admin_user):
    from app.auth import verify_password, hash_password
    from app.database import get_db
    from app.models import User

    with get_db() as db:
        db_user = db.query(User).filter(User.id == admin_user.id).first()
        db_user.password_hash = hash_password("oldpass")
        db.commit()

    resp = client.post(
        "/auth/change-password",
        json={
            "current_password": "oldpass",
            "new_password": "newpass",
            "new_password_confirm": "newpass",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    from app.database import get_db
    from app.models import User

    with get_db() as db:
        db_user = db.query(User).filter(User.id == admin_user.id).first()
        assert verify_password("newpass", db_user.password_hash)


def test_change_own_email(client, auth_headers, admin_user):
    from app.auth import hash_password
    from app.database import get_db
    from app.models import User

    with get_db() as db:
        db_user = db.query(User).filter(User.id == admin_user.id).first()
        db_user.password_hash = hash_password("admin123")
        db.commit()

    resp = client.post(
        "/auth/change-email",
        json={
            "password": "admin123",
            "new_email": "newemail@test.com",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    from app.database import get_db
    from app.models import User

    with get_db() as db:
        db_user = db.query(User).filter(User.id == admin_user.id).first()
        assert db_user.email == "newemail@test.com"


def test_admin_change_password(client, auth_headers, normal_user):
    resp = client.post(
        f"/auth/admin/{normal_user.id}/change-password",
        json={
            "new_password": "adminchanged",
            "new_password_confirm": "adminchanged",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_admin_change_email(client, auth_headers, normal_user):
    resp = client.post(
        f"/auth/admin/{normal_user.id}/change-email",
        json={
            "new_email": "changed@test.com",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_admin_tokens_page(client, auth_headers):
    resp = client.get("/auth/admin/tokens", headers=auth_headers)
    assert resp.status_code == 200


def test_admin_register_token_generation(client, auth_headers):
    resp = client.post(
        "/auth/register/token",
        json={"expires_in": "7d"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "token" in data


def test_non_admin_cannot_generate_token(client, user_token):
    resp = client.post(
        "/auth/register/token",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_admin_delete_token(client, auth_headers, admin_user):
    from app.database import get_db
    from app.models import InviteToken

    with get_db() as db:
        t = InviteToken(token="delete-me-token", created_by_id=admin_user.id)
        db.add(t)
        db.commit()
        token_id = t.id

    resp = client.delete(
        f"/auth/admin/tokens/{token_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200

    with get_db() as db:
        assert db.query(InviteToken).filter(InviteToken.id == token_id).first() is None


def test_admin_update_token_expiry(client, auth_headers, admin_user):
    from app.database import get_db
    from app.models import InviteToken

    with get_db() as db:
        t = InviteToken(token="update-me-token", created_by_id=admin_user.id)
        db.add(t)
        db.commit()
        token_id = t.id

    resp = client.put(
        f"/auth/admin/tokens/{token_id}",
        json={"expires_in": "24h"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    with get_db() as db:
        t = db.query(InviteToken).filter(InviteToken.id == token_id).first()
        assert t.expires_at is not None


def test_validate_token_valid(client, admin_user):
    from app.database import get_db
    from app.models import InviteToken

    with get_db() as db:
        t = InviteToken(token="validate-valid", created_by_id=admin_user.id)
        db.add(t)
        db.commit()

    resp = client.get("/auth/register/token/validate?token=validate-valid")
    assert resp.status_code == 200
    assert resp.get_json() == {"valid": True}


def test_validate_token_invalid(client):
    resp = client.get("/auth/register/token/validate?token=nonexistent")
    assert resp.status_code == 200
    assert resp.get_json() == {"valid": False}


def test_non_admin_cannot_access_admin_tokens(client, user_token):
    resp = client.get(
        "/auth/admin/tokens", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert resp.status_code == 403


def test_non_admin_cannot_change_other_password(client, user_token, normal_user):
    resp = client.post(
        f"/auth/admin/{normal_user.id}/change-password",
        json={
            "new_password": "test",
            "new_password_confirm": "test",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_non_admin_cannot_change_other_email(client, user_token, normal_user):
    resp = client.post(
        f"/auth/admin/{normal_user.id}/change-email",
        json={
            "new_email": "test@test.com",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403
