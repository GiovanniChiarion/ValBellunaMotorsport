from datetime import UTC, datetime

from app import create_app
from app.database import get_db
from app.models import AuditLog, User


def _last_log(db):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .first()
    )


def test_login_success_logs_action(client, app):
    resp = client.post(
        "/auth/login",
        json={"email": "superadmin@valbellunamotorsport.it", "password": "superadmin123"},
        headers={"X-Forwarded-For": "10.0.0.1"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "LOGIN"
        assert log.entity_type == "auth"
        assert log.ip_address == "10.0.0.1"
        assert "SuperAdmin" in (log.description or "")
        assert log.user_id is not None


def test_login_failure_logs_action(client, app):
    resp = client.post(
        "/auth/login",
        json={"email": "nonexistent@test.com", "password": "wrong"},
        headers={"X-Forwarded-For": "10.0.0.2"},
    )
    assert resp.status_code == 401

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "LOGIN_FAILED"
        assert log.entity_type == "auth"
        assert log.ip_address == "10.0.0.2"
        assert log.description is not None
        assert log.user_id is None


def test_logout_logs_action(client, app, admin_token):
    resp = client.post(
        "/auth/logout",
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Forwarded-For": "10.0.0.3",
        },
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "LOGOUT"
        assert log.entity_type == "auth"
        assert log.ip_address == "10.0.0.3"


def test_register_logs_action(client, app, admin_token, admin_user):
    from app.database import get_db
    from app.models import InviteToken

    with get_db() as db:
        t = InviteToken(token="test-reg-token-db", created_by_id=admin_user.id)
        db.add(t)
        db.commit()

    resp = client.post(
        "/auth/register",
        json={
            "nome": "Nuovo Utente",
            "email": "nuovo@test.com",
            "password": "password123",
            "token": "test-reg-token-db",
        },
        headers={"X-Forwarded-For": "10.0.0.4"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "REGISTER"
        assert log.entity_type == "user"
        assert log.ip_address == "10.0.0.4"
        assert "Nuovo Utente" in (log.description or "")


def test_token_generation_logs_action(client, admin_token):
    resp = client.post(
        "/auth/register/token",
        json={"expires_in": "7d"},
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Forwarded-For": "10.0.0.5",
        },
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "TOKEN_GENERATE"
        assert log.entity_type == "auth"
        assert log.ip_address == "10.0.0.5"


def test_password_change_logs_action(client, app, normal_user, user_token):
    resp = client.post(
        "/auth/change-password",
        json={
            "current_password": "password123",
            "new_password": "newpass123",
            "new_password_confirm": "newpass123",
        },
        headers={"Authorization": f"Bearer {user_token}", "X-Forwarded-For": "10.0.0.6"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "PASSWORD_CHANGE"
        assert log.entity_type == "user"
        assert log.user_id == normal_user.id
        assert log.ip_address == "10.0.0.6"


def test_email_change_logs_action(client, app, normal_user, user_token):
    resp = client.post(
        "/auth/change-email",
        json={"password": "password123", "new_email": "nuova@test.com"},
        headers={"Authorization": f"Bearer {user_token}", "X-Forwarded-For": "10.0.0.7"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "EMAIL_CHANGE"
        assert log.entity_type == "user"
        assert log.user_id == normal_user.id
        assert log.ip_address == "10.0.0.7"


def test_admin_delete_user_logs_action(client, admin_token, normal_user, app):
    resp = client.post(
        f"/auth/admin/{normal_user.id}/delete",
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.8"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "DELETE"
        assert log.entity_type == "user"
        assert log.ip_address == "10.0.0.8"
        assert normal_user.nome in (log.description or "")
