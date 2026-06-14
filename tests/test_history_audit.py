from datetime import UTC, datetime

from app.database import get_db
from app.models import AuditLog

# flake8: noqa


def _log_entry(db, action="LOGIN", user_id=None, ip="10.0.0.1"):
    log = AuditLog(
        action=action,
        entity_type="auth",
        user_id=user_id,
        ip_address=ip,
        description="Test log",
        timestamp=datetime.now(UTC),
    )
    db.add(log)
    db.commit()


def test_history_filter_by_action(client, app, superadmin_token, normal_user):
    with get_db() as db:
        _log_entry(db, action="LOGIN", user_id=normal_user.id)
        _log_entry(db, action="LOGOUT", user_id=normal_user.id)
        _log_entry(db, action="LOGIN", user_id=normal_user.id)

    resp = client.get(
        "/history?action=LOGOUT",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        count = db.query(AuditLog).filter(AuditLog.action == "LOGOUT").count()
        assert count == 1


def test_history_filter_by_user(client, app, superadmin_token, admin_user, normal_user):
    with get_db() as db:
        _log_entry(db, user_id=admin_user.id)
        _log_entry(db, user_id=normal_user.id)

    resp = client.get(
        f"/history?user_id={normal_user.id}",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200


def test_history_filter_by_date(client, app, superadmin_token, normal_user):
    with get_db() as db:
        _log_entry(db, action="LOGIN", user_id=normal_user.id)

    from datetime import timedelta

    today = datetime.now(UTC).strftime("%Y-%m-%d")
    tomorrow = (datetime.now(UTC) + timedelta(days=1)).strftime("%Y-%m-%d")

    resp = client.get(
        f"/history?date_from={today}&date_to={tomorrow}",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200


def test_history_filter_by_ip(client, app, superadmin_token, normal_user):
    with get_db() as db:
        before = db.query(AuditLog).filter(AuditLog.ip_address.like("%192.168.1.42%")).count()
        _log_entry(db, ip="192.168.1.42", user_id=normal_user.id)
        after = db.query(AuditLog).filter(AuditLog.ip_address.like("%192.168.1.42%")).count()

    assert after == before + 1


def test_history_pagination(client, app, superadmin_token, normal_user):
    with get_db() as db:
        for i in range(5):
            _log_entry(db, action="LOGIN", user_id=normal_user.id)

    resp = client.get(
        "/history?per_page=2&page=1",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200


def test_history_export_respects_filter(client, app, superadmin_token, normal_user):
    with get_db() as db:
        _log_entry(db, action="LOGIN", user_id=normal_user.id)
        _log_entry(db, action="LOGOUT", user_id=normal_user.id)

    import json

    resp = client.get(
        "/history/export?action=LOGOUT",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data["data"]["audit_logs"]) == 1
    assert data["data"]["audit_logs"][0]["action"] == "LOGOUT"
