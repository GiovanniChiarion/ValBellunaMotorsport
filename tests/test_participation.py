def test_set_participation(client, auth_headers, admin_user):
    from app.database import get_db
    from app.models import Race
    from datetime import date

    with get_db() as db:
        race = Race(
            descrizione="Test Race", data_inizio=date.today(), stato="Confermato"
        )
        db.add(race)
        db.commit()
        race_id = race.id

    resp = client.post(
        f"/participation/{race_id}",
        json={
            "status": "si",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_update_nota(client, auth_headers, admin_user):
    from app.database import get_db
    from app.models import Participation, Race
    from datetime import date

    with get_db() as db:
        race = Race(
            descrizione="Test Race", data_inizio=date.today(), stato="Confermato"
        )
        db.add(race)
        db.commit()
        race_id = race.id
        part = Participation(user_id=admin_user.id, race_id=race_id, status="si")
        db.add(part)
        db.commit()

    resp = client.post(
        f"/participation/{race_id}/nota",
        json={"nota": "My personal note"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_toggle_macchina(client, auth_headers, admin_user):
    from app.database import get_db
    from app.models import Participation, Race
    from datetime import date

    with get_db() as db:
        race = Race(
            descrizione="Test Race", data_inizio=date.today(), stato="Confermato"
        )
        db.add(race)
        db.commit()
        race_id = race.id
        part = Participation(user_id=admin_user.id, race_id=race_id, status="si")
        db.add(part)
        db.commit()

    resp = client.post(f"/participation/{race_id}/macchina", headers=auth_headers)
    assert resp.status_code == 200


def test_admin_set_participation(client, auth_headers, normal_user, admin_user):
    from app.database import get_db
    from app.models import Race
    from datetime import date

    with get_db() as db:
        race = Race(
            descrizione="Test Race", data_inizio=date.today(), stato="Confermato"
        )
        db.add(race)
        db.commit()
        race_id = race.id

    resp = client.post(
        f"/participation/admin/{normal_user.id}/{race_id}",
        json={
            "status": "no",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_set_participation_unauthenticated(client):
    resp = client.post("/participation/1", json={"status": "si"})
    assert resp.status_code == 401
