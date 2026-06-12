def test_history_view(client, auth_headers):
    resp = client.get("/history", headers=auth_headers)
    assert resp.status_code == 200


def test_history_requires_admin(client, user_token):
    resp = client.get("/history", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_history_export(client, superadmin_token):
    resp = client.get(
        "/history/export", headers={"Authorization": f"Bearer {superadmin_token}"}
    )
    assert resp.status_code == 200


def test_history_export_requires_superadmin(client, auth_headers):
    resp = client.get("/history/export", headers=auth_headers)
    assert resp.status_code == 403
