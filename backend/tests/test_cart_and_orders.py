def test_cart_requires_auth(client):
    resp = client.get("/cart")
    assert resp.status_code == 401


def test_add_item_and_view_cart(client, customer, product):
    resp = client.post(
        "/cart/items",
        json={"product_id": product["id"], "quantity": 2},
        headers=customer["headers"],
    )
    assert resp.status_code == 200
    cart = resp.json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 2


def test_add_item_insufficient_stock_rejected(client, customer, product):
    # product["stock"] es 5 (ver fixture); pedimos mas que eso pero
    # dentro del tope de cantidad del schema (<=100) para probar la
    # regla de negocio (stock) y no la validacion de entrada.
    resp = client.post(
        "/cart/items",
        json={"product_id": product["id"], "quantity": product["stock"] + 3},
        headers=customer["headers"],
    )
    assert resp.status_code == 400


def test_update_and_remove_cart_item(client, customer, product):
    add = client.post(
        "/cart/items", json={"product_id": product["id"], "quantity": 1}, headers=customer["headers"]
    )
    item_id = add.json()["items"][0]["id"]

    update = client.put(
        f"/cart/items/{item_id}", json={"quantity": 3}, headers=customer["headers"]
    )
    assert update.json()["items"][0]["quantity"] == 3

    remove = client.delete(f"/cart/items/{item_id}", headers=customer["headers"])
    assert remove.json()["items"] == []


def test_checkout_creates_order_and_decrements_stock(client, customer, product):
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2}, headers=customer["headers"])

    resp = client.post(
        "/orders", json={"shipping_address": "Calle Falsa 123"}, headers=customer["headers"]
    )
    assert resp.status_code == 201
    order = resp.json()
    assert order["status"] == "pending"
    assert order["total_amount"] == 2 * product["price"]

    # el stock del producto se descuenta
    product_after = client.get(f"/products/{product['id']}").json()
    assert product_after["stock"] == product["stock"] - 2

    # el carrito queda vacio despues del checkout
    cart_after = client.get("/cart", headers=customer["headers"]).json()
    assert cart_after["items"] == []


def test_checkout_with_empty_cart_rejected(client, customer):
    resp = client.post("/orders", json={"shipping_address": "Test 123"}, headers=customer["headers"])
    assert resp.status_code == 400


def test_customer_cannot_see_others_order(client, customer, admin, product):
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1}, headers=customer["headers"])
    order = client.post(
        "/orders", json={"shipping_address": "Test 123"}, headers=customer["headers"]
    ).json()

    other_payload = {"email": "otro@test.com", "full_name": "Otro", "password": "Segura123"}
    client.post("/auth/register", json=other_payload)
    other_token = client.post(
        "/auth/login", data={"username": other_payload["email"], "password": other_payload["password"]}
    ).json()["access_token"]

    resp = client.get(f"/orders/{order['id']}", headers={"Authorization": f"Bearer {other_token}"})
    assert resp.status_code == 404


def test_admin_sees_all_orders(client, customer, admin, product):
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1}, headers=customer["headers"])
    client.post("/orders", json={"shipping_address": "Test 123"}, headers=customer["headers"])

    resp = client.get("/orders/admin/all", headers=admin["headers"])
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_customer_cannot_list_all_orders(client, customer):
    resp = client.get("/orders/admin/all", headers=customer["headers"])
    assert resp.status_code == 403
