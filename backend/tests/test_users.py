def test_customer_cannot_list_users(client, customer):
    resp = client.get("/users", headers=customer["headers"])
    assert resp.status_code == 403


def test_admin_can_list_users(client, admin, customer):
    resp = client.get("/users", headers=admin["headers"])
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "admin@test.com" in emails
    assert "cliente@test.com" in emails


def test_admin_can_deactivate_other_user(client, admin, customer):
    me = client.get("/auth/me", headers=customer["headers"]).json()

    resp = client.patch(f"/users/{me['id']}", json={"is_active": False}, headers=admin["headers"])
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # el usuario desactivado ya no puede loguearse a partir de ahora
    login = client.post(
        "/auth/login", data={"username": "cliente@test.com", "password": "Segura123"}
    )
    assert login.status_code == 403


def test_admin_can_promote_user_to_admin(client, admin, customer):
    me = client.get("/auth/me", headers=customer["headers"]).json()

    resp = client.patch(f"/users/{me['id']}", json={"role": "admin"}, headers=admin["headers"])
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_admin_cannot_deactivate_self(client, admin):
    me = client.get("/auth/me", headers=admin["headers"]).json()

    resp = client.patch(f"/users/{me['id']}", json={"is_active": False}, headers=admin["headers"])
    assert resp.status_code == 400


def test_admin_cannot_demote_self(client, admin):
    me = client.get("/auth/me", headers=admin["headers"]).json()

    resp = client.patch(f"/users/{me['id']}", json={"role": "customer"}, headers=admin["headers"])
    assert resp.status_code == 400


def test_update_nonexistent_user_404(client, admin):
    resp = client.patch("/users/9999", json={"is_active": False}, headers=admin["headers"])
    assert resp.status_code == 404
