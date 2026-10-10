def test_list_products_public(client, product):
    resp = client.get("/products")
    assert resp.status_code == 200
    body = resp.json()
    names = [p["name"] for p in body["items"]]
    assert "Whey Test" in names
    assert body["total"] >= 1


def test_list_products_pagination_metadata(client, admin, category):
    for i in range(3):
        client.post(
            "/products",
            json={
                "name": f"Producto {i}",
                "slug": f"producto-{i}",
                "price": 1000,
                "stock": 5,
                "category_id": category["id"],
            },
            headers=admin["headers"],
        )

    resp = client.get("/products", params={"page": 1, "page_size": 2})
    body = resp.json()
    assert body["page"] == 1
    assert body["page_size"] == 2
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["total_pages"] == 2

    page2 = client.get("/products", params={"page": 2, "page_size": 2}).json()
    assert len(page2["items"]) == 1


def test_get_product_not_found(client):
    resp = client.get("/products/9999")
    assert resp.status_code == 404


def test_customer_cannot_create_product(client, customer, category):
    resp = client.post(
        "/products",
        json={"name": "X", "slug": "x", "price": 10, "stock": 1, "category_id": category["id"]},
        headers=customer["headers"],
    )
    assert resp.status_code == 403


def test_admin_can_create_and_update_product(client, admin, category):
    create = client.post(
        "/products",
        json={"name": "Creatina", "slug": "creatina-t", "price": 5000, "stock": 10, "category_id": category["id"]},
        headers=admin["headers"],
    )
    assert create.status_code == 201
    product_id = create.json()["id"]

    update = client.put(
        f"/products/{product_id}",
        json={"price": 5500},
        headers=admin["headers"],
    )
    assert update.status_code == 200
    assert update.json()["price"] == 5500.0


def test_admin_delete_is_soft_delete(client, admin, product):
    resp = client.delete(f"/products/{product['id']}", headers=admin["headers"])
    assert resp.status_code == 204

    listing = client.get("/products")
    ids = [p["id"] for p in listing.json()["items"]]
    assert product["id"] not in ids


def test_product_discount_computes_final_price(client, admin, product):
    resp = client.put(
        f"/products/{product['id']}",
        json={"discount_percentage": 20},
        headers=admin["headers"],
    )
    body = resp.json()
    assert body["discount_percentage"] == 20
    assert body["final_price"] == round(product["price"] * 0.8, 2)


def test_discount_out_of_range_rejected(client, admin, product):
    resp = client.put(
        f"/products/{product['id']}",
        json={"discount_percentage": 95},
        headers=admin["headers"],
    )
    assert resp.status_code == 422


def test_no_discount_final_price_equals_price(client, product):
    resp = client.get(f"/products/{product['id']}")
    body = resp.json()
    assert body["discount_percentage"] == 0
    assert body["final_price"] == body["price"]


def test_new_products_ordered_by_creation(client, admin, category, product):
    resp = client.post(
        "/products",
        json={"name": "Recien llegado", "slug": "recien-llegado", "price": 5000, "stock": 10, "category_id": category["id"]},
        headers=admin["headers"],
    )
    newest = resp.json()

    listing = client.get("/products/new").json()
    slugs = [p["slug"] for p in listing]
    assert slugs[0] == newest["slug"]
    assert product["slug"] in slugs


def test_on_sale_only_returns_discounted_products(client, admin, category, product):
    client.put(f"/products/{product['id']}", json={"discount_percentage": 15}, headers=admin["headers"])
    client.post(
        "/products",
        json={"name": "Sin descuento", "slug": "sin-descuento", "price": 3000, "stock": 10, "category_id": category["id"]},
        headers=admin["headers"],
    )

    listing = client.get("/products/on-sale").json()
    slugs = [p["slug"] for p in listing]
    assert product["slug"] in slugs
    assert "sin-descuento" not in slugs


def test_featured_falls_back_to_newest_without_sales(client, product):
    listing = client.get("/products/featured").json()
    assert any(p["slug"] == product["slug"] for p in listing)


def test_featured_prioritizes_best_sellers(client, admin, customer, category, product):
    other = client.post(
        "/products",
        json={"name": "Poco vendido", "slug": "poco-vendido", "price": 2000, "stock": 10, "category_id": category["id"]},
        headers=admin["headers"],
    ).json()

    # se compra 3 unidades del producto original, 0 del otro
    client.post("/cart/items", json={"product_id": product["id"], "quantity": 3}, headers=customer["headers"])
    order = client.post("/orders", json={"shipping_address": "Test 123"}, headers=customer["headers"]).json()
    client.patch(f"/orders/{order['id']}/status", json={"status": "paid"}, headers=admin["headers"])

    listing = client.get("/products/featured", params={"limit": 1}).json()
    assert listing[0]["slug"] == product["slug"]


def test_admin_all_products_includes_inactive(client, admin, product):
    client.delete(f"/products/{product['id']}", headers=admin["headers"])

    public_listing = client.get("/products").json()["items"]
    assert product["id"] not in [p["id"] for p in public_listing]

    admin_listing = client.get("/products/admin/all", headers=admin["headers"]).json()
    ids = [p["id"] for p in admin_listing]
    assert product["id"] in ids
    assert next(p for p in admin_listing if p["id"] == product["id"])["is_active"] is False


def test_customer_cannot_list_admin_products(client, customer):
    resp = client.get("/products/admin/all", headers=customer["headers"])
    assert resp.status_code == 403
