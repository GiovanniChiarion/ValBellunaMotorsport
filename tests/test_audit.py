from flask import Flask

from app.audit import log_action
from app.models import AuditLog


def test_log_action_creates_entry(app: Flask, db, normal_user):
    with app.test_request_context():
        log = log_action(
            db=db,
            action="LOGIN",
            entity_type="auth",
            user_id=normal_user.id,
            description="Test user ha effettuato l'accesso",
            actor_name=normal_user.nome,
            ip_address="192.168.1.1",
            user_agent="test-agent",
        )

    assert log.id is not None
    assert log.action == "LOGIN"
    assert log.entity_type == "auth"
    assert log.user_id == normal_user.id
    assert log.description == "Test user ha effettuato l'accesso"
    assert log.actor_name == normal_user.nome
    assert log.ip_address == "192.168.1.1"
    assert log.user_agent == "test-agent"
    assert log.field is None
    assert log.old_value is None
    assert log.new_value is None
    assert log.race_id is None


def test_log_action_auto_ip(app: Flask, db, normal_user):
    with app.test_request_context(headers={"X-Forwarded-For": "10.0.0.1, proxy"}):
        log = log_action(
            db=db,
            action="LOGIN",
            user_id=normal_user.id,
        )

    assert log.ip_address == "10.0.0.1"
    assert log.action == "LOGIN"


def test_log_action_auto_user_from_g(app: Flask, db, normal_user):
    with app.test_request_context():
        from flask import g

        g.current_user = normal_user

        log = log_action(
            db=db,
            action="LOGOUT",
        )

    assert log.user_id == normal_user.id
    assert log.actor_name == normal_user.nome


def test_log_action_preserves_field_values(app: Flask, db, normal_user):
    with app.test_request_context():
        log = log_action(
            db=db,
            action="UPDATE",
            entity_type="participation",
            user_id=normal_user.id,
            field="participation.status",
            old_value="indeciso",
            new_value="si",
        )

    assert log.field == "participation.status"
    assert log.old_value == "indeciso"
    assert log.new_value == "si"
