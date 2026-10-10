def _pay_order(client, admin, order_id):
    return client.patch(f"/orders/{order_id}/status", json={"status": "paid"}, headers=admin["headers"])


def test_customer_cannot_view_stats(client, customer):
    assert client.get("/admin/stats/summary", headers=customer["headers"]).status_code == 403
    assert client.get("/admin/stats/sales-by-date", headers=customer["headers"]).status_code == 403
    assert client.get("/admin/stats/top-products", headers=customer["headers"]).status_code == 403


def test_summary_with_no_sales(client, admin, product):
    resp = client.get("/admin/stats/summary", headers=admin["headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 0
    assert body["total_orders"] == 0
    assert body["active_products"] == 1
    assert body["total_customers"] == 1  # el propio admin cuenta como usuario


def test_summary_reflects_low_stock(client, admin, category):
    client.post(
        "/products",
        json={"name": "Bajo stock", "slug": "bajo-stock", "price": 1000, "stock": 2, "category_id": category["id"]},
        headers=admin["headers"],
    )
    resp = client.get("/admin/stats/summary", headers=admin["headers"]).json()
    assert resp["low_stock_products"] == 1


def test_stats_after_paid_order(client, admin, customer, product):
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 2}, headers=customer["headers"])
    order = client.post(
        "/orders", json={"shipping_address": "Test 123"}, headers=customer["headers"]
    ).json()

    pay = _pay_order(client, admin, order["id"])
    assert pay.status_code == 200

    summary = client.get("/admin/stats/summary", headers=admin["headers"]).json()
    assert summary["total_orders"] == 1
    assert summary["paid_orders"] == 1
    assert summary["total_revenue"] == 2 * product["price"]

    by_date = client.get("/admin/stats/sales-by-date", headers=admin["headers"]).json()
    assert len(by_date) == 1
    assert by_date[0]["revenue"] == 2 * product["price"]

    top = client.get("/admin/stats/top-products", headers=admin["headers"]).json()
    assert len(top) == 1
    assert top[0]["product_id"] == product["id"]
    assert top[0]["quantity_sold"] == 2


def test_cancelled_order_does_not_count_as_revenue(client, admin, customer, product):
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 1}, headers=customer["headers"])
    order = client.post(
        "/orders", json={"shipping_address": "Test 123"}, headers=customer["headers"]
    ).json()
    client.patch(f"/orders/{order['id']}/status", json={"status": "cancelled"}, headers=admin["headers"])

    summary = client.get("/admin/stats/summary", headers=admin["headers"]).json()
    assert summary["total_revenue"] == 0
    assert summary["cancelled_orders"] == 1
