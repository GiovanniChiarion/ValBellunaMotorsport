def test_reports_index(client, auth_headers):
    resp = client.get("/reports", headers=auth_headers)
    assert resp.status_code == 200


def test_reports_requires_admin(client, user_token):
    resp = client.get("/reports", headers={"Authorization": f"Bearer {user_token}"})
    assert resp.status_code == 403


def test_reports_unauthenticated(client):
    resp = client.get("/reports")
    assert resp.status_code == 401
