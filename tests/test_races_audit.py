from app.database import get_db
from app.models import AuditLog


def _last_log(db):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .first()
    )


def _last_n_logs(db, n):
    return (
        db.query(AuditLog)
        .order_by(AuditLog.id.desc())
        .limit(n)
        .all()
    )


def test_create_race_logs_action(client, admin_token):
    resp = client.post(
        "/races",
        json={
            "data_inizio": "2026-07-01",
            "descrizione": "Gara di test",
            "stato": "Confermato",
        },
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.10"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "CREATE"
        assert log.entity_type == "race"
        assert log.field == "descrizione"
        assert log.new_value == "Gara di test"
        assert log.ip_address == "10.0.0.10"


def test_delete_race_logs_action(client, admin_token, app):
    with get_db() as db:
        from app.models import Race
        from datetime import date

        race = Race(data_inizio=date(2026, 8, 1), descrizione="Gara da eliminare")
        db.add(race)
        db.commit()
        race_id = race.id

    resp = client.post(
        f"/races/{race_id}/delete",
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.11"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "DELETE"
        assert log.entity_type == "race"
        assert log.entity_id == race_id
        assert log.ip_address == "10.0.0.11"
        assert "Gara da eliminare" in (log.description or "")


def test_edit_race_logs_action(client, admin_token, app):
    with get_db() as db:
        from app.models import Race
        from datetime import date

        race = Race(data_inizio=date(2026, 8, 1), descrizione="Gara originale")
        db.add(race)
        db.commit()
        race_id = race.id

    resp = client.post(
        f"/races/{race_id}/edit",
        json={"descrizione": "Gara modificata", "stato": "Confermato"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.12"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        logs = db.query(AuditLog).filter(AuditLog.race_id == race_id).order_by(AuditLog.id.desc()).all()
        assert len(logs) >= 1
        for log in logs:
            assert log.action == "UPDATE" or log.action is None
            assert log.race_id == race_id


def test_create_race_type_logs_action(client, admin_token):
    resp = client.post(
        "/races/admin/types",
        json={"codice": "TEST", "descrizione": "Tipo di test"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.13"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "CREATE"
        assert log.entity_type == "race_type"
        assert log.ip_address == "10.0.0.13"


def test_delete_race_type_logs_action(client, admin_token, app):
    with get_db() as db:
        from app.models import RaceType

        rt = RaceType(codice="DEL", descrizione="Da eliminare")
        db.add(rt)
        db.commit()
        type_id = rt.id

    resp = client.post(
        f"/races/admin/types/{type_id}/delete",
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.14"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "DELETE"
        assert log.entity_type == "race_type"
        assert log.ip_address == "10.0.0.14"


def test_export_data_logs_action(client, superadmin_token):
    resp = client.get(
        "/races/admin/export",
        headers={
            "Authorization": f"Bearer {superadmin_token}",
            "X-Forwarded-For": "10.0.0.15",
        },
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "EXPORT"
        assert log.entity_type == "system"
        assert log.ip_address == "10.0.0.15"


def test_import_data_logs_action(client, superadmin_token):
    import io
    import json

    backup = json.dumps({
        "data": {
            "race_types": [],
            "users": [],
            "races": [],
            "participations": [],
            "audit_logs": [],
        }
    })

    resp = client.post(
        "/races/admin/import",
        data={"file": (io.BytesIO(backup.encode()), "backup.json")},
        headers={"Authorization": f"Bearer {superadmin_token}", "X-Forwarded-For": "10.0.0.16"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "IMPORT"
        assert log.entity_type == "system"
        assert log.ip_address == "10.0.0.16"


def test_admin_set_role_logs_action(client, admin_token, normal_user, app):
    resp = client.post(
        f"/races/admin/members/{normal_user.id}/role",
        json={"ruolo": "admin"},
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.17"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "ROLE_CHANGE"
        assert log.entity_type == "user"
        assert log.entity_id == normal_user.id
        assert log.old_value == "membro"
        assert log.new_value == "admin"
        assert log.ip_address == "10.0.0.17"


def test_admin_toggle_user_logs_action(client, admin_token, normal_user, app):
    resp = client.post(
        f"/races/admin/members/{normal_user.id}/toggle",
        headers={"Authorization": f"Bearer {admin_token}", "X-Forwarded-For": "10.0.0.18"},
    )
    assert resp.status_code == 200

    with get_db() as db:
        log = _last_log(db)
        assert log is not None
        assert log.action == "USER_TOGGLE"
        assert log.entity_type == "user"
        assert log.entity_id == normal_user.id
        assert log.ip_address == "10.0.0.18"
