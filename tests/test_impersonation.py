def test_impersonate_not_available_for_admin(client, admin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 403


def test_impersonate_not_available_for_user(client, user_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403


def test_superadmin_impersonate_admin(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "admin"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["effective_role"] == "admin"


def test_superadmin_impersonate_membro(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["effective_role"] == "membro"


def test_superadmin_revert_impersonation(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["effective_role"] == "membro"

    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": None},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["effective_role"] == "superadmin"


def test_invalid_role_rejected(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "invalid"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 400


def test_impersonated_membro_cannot_access_admin(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/races/admin/dashboard",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 403


def test_impersonated_admin_cannot_access_superadmin(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "admin"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/history",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 403


def test_impersonated_admin_can_access_admin_routes(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "admin"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/races/admin/dashboard",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200


def test_reverted_superadmin_regains_access(client, superadmin_token):
    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": "membro"},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.post(
        "/auth/impersonate",
        json={"ruolo": None},
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200

    resp = client.get(
        "/history",
        headers={"Authorization": f"Bearer {superadmin_token}"},
    )
    assert resp.status_code == 200
