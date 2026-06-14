def test_calendar_view(client, auth_headers):
    resp = client.get("/races", headers=auth_headers)
    assert resp.status_code == 200


def test_race_detail_not_found(client, auth_headers):
    resp = client.get("/races/999", headers=auth_headers)
    assert resp.status_code == 404


def test_admin_dashboard(client, auth_headers):
    resp = client.get("/races/admin/dashboard", headers=auth_headers)
    assert resp.status_code == 200


def test_new_race_page(client, auth_headers):
    resp = client.get("/races/admin/new", headers=auth_headers)
    assert resp.status_code == 200


def test_create_race(client, auth_headers):
    resp = client.post(
        "/races",
        json={
            "descrizione": "Test Race",
            "stato": "Confermato",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "race" in data


def test_create_race_and_edit(client, auth_headers):
    from app.database import get_db
    from app.models import Race

    resp = client.post(
        "/races",
        json={
            "descrizione": "Original Race",
            "stato": "In attesa di conferma",
        },
        headers=auth_headers,
    )
    race_id = resp.get_json()["race"]["id"]

    resp = client.post(
        f"/races/{race_id}/edit",
        json={
            "descrizione": "Updated Race",
            "stato": "Confermato",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200

    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        assert race.descrizione == "Updated Race"
        assert race.stato == "Confermato"


def test_delete_race(client, auth_headers):
    from app.database import get_db
    from app.models import Race

    resp = client.post(
        "/races",
        json={
            "descrizione": "Delete Me",
            "stato": "In attesa di conferma",
        },
        headers=auth_headers,
    )
    race_id = resp.get_json()["race"]["id"]

    resp = client.post(f"/races/{race_id}/delete", headers=auth_headers)
    assert resp.status_code == 200

    with get_db() as db:
        race = db.query(Race).filter(Race.id == race_id).first()
        assert race is None


def test_admin_list_races(client, auth_headers):
    resp = client.get("/races/admin/list", headers=auth_headers)
    assert resp.status_code == 200


def test_admin_members(client, auth_headers):
    resp = client.get("/races/admin/members", headers=auth_headers)
    assert resp.status_code == 200


def test_admin_set_role(client, auth_headers, normal_user):
    resp = client.post(
        f"/races/admin/members/{normal_user.id}/role",
        json={
            "ruolo": "admin",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_admin_toggle_user(client, auth_headers, normal_user):
    resp = client.post(
        f"/races/admin/members/{normal_user.id}/toggle", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert "attivo" in data


def test_admin_race_types_page(client, auth_headers):
    resp = client.get("/races/admin/types", headers=auth_headers)
    assert resp.status_code == 200


def test_create_race_type(client, auth_headers):
    resp = client.post(
        "/races/admin/types",
        json={
            "codice": "TEST",
            "descrizione": "Test Type",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_delete_race_type(client, auth_headers):
    from app.database import get_db
    from app.models import RaceType

    with get_db() as db:
        rt = RaceType(codice="DEL", descrizione="Delete Me")
        db.add(rt)
        db.commit()
        type_id = rt.id

    resp = client.post(f"/races/admin/types/{type_id}/delete", headers=auth_headers)
    assert resp.status_code == 200

    with get_db() as db:
        assert db.query(RaceType).filter(RaceType.id == type_id).first() is None


def test_export_data(client, superadmin_token):
    resp = client.get(
        "/races/admin/export", headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert resp.status_code == 200


def test_export_requires_superadmin(client, auth_headers):
    resp = client.get("/races/admin/export", headers=auth_headers)
    assert resp.status_code == 403


def test_import_data(client, superadmin_token):
    import io
    import json

    backup = json.dumps(
        {
            "data": {
                "race_types": [{"codice": "IMP", "descrizione": "Imported"}],
            }
        }
    )
    data = {"file": (io.BytesIO(backup.encode()), "backup.json")}
    resp = client.post(
        "/races/admin/import",
        data=data,
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200


def test_calendar_view_filter_enabled_for_superadmin(client, superadmin_token):
    resp = client.get("/races", headers={"Authorization": f"Bearer {superadmin_token}"})
    assert resp.status_code == 200
    assert b"filterMatches" in resp.data


def test_calendar_view_filter_disabled_for_admin(client, auth_headers):
    resp = client.get("/races", headers=auth_headers)
    assert resp.status_code == 200
    assert b"filterMatches" not in resp.data
