def test_register_success(client):
    resp = client.post(
        "/auth/register",
        json={"email": "nuevo@test.com", "full_name": "Nuevo Usuario", "password": "Segura123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "nuevo@test.com"
    assert body["role"] == "customer"
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_duplicate_email_rejected(client):
    payload = {"email": "dup@test.com", "full_name": "Uno", "password": "Segura123"}
    client.post("/auth/register", json=payload)
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 400


def test_register_weak_password_rejected(client):
    resp = client.post(
        "/auth/register",
        json={"email": "debil@test.com", "full_name": "Debil", "password": "sololetras"},
    )
    assert resp.status_code == 422


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={"email": "loginfail@test.com", "full_name": "X", "password": "Segura123"},
    )
    resp = client.post(
        "/auth/login",
        data={"username": "loginfail@test.com", "password": "incorrecta"},
    )
    assert resp.status_code == 401


def test_login_success_and_me(client, customer):
    resp = client.get("/auth/me", headers=customer["headers"])
    assert resp.status_code == 200
    assert resp.json()["email"] == customer["email"]


def test_me_without_token_returns_401(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401
