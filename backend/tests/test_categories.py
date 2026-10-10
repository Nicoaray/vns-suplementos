def test_list_categories_public(client, category):
    resp = client.get("/categories")
    assert resp.status_code == 200
    slugs = [c["slug"] for c in resp.json()]
    assert "proteinas" in slugs


def test_customer_cannot_create_category(client, customer):
    resp = client.post(
        "/categories",
        json={"name": "X", "slug": "x", "description": "test"},
        headers=customer["headers"],
    )
    assert resp.status_code == 403


def test_admin_can_create_category(client, admin):
    resp = client.post(
        "/categories",
        json={"name": "Vitaminas", "slug": "vitaminas", "description": "Multivitaminicos"},
        headers=admin["headers"],
    )
    assert resp.status_code == 201
    assert resp.json()["slug"] == "vitaminas"


def test_duplicate_category_slug_returns_400(client, admin, category):
    resp = client.post(
        "/categories",
        json={"name": "Proteinas 2", "slug": "proteinas", "description": "dup"},
        headers=admin["headers"],
    )
    assert resp.status_code == 400


def test_duplicate_category_name_returns_400(client, admin, category):
    resp = client.post(
        "/categories",
        json={"name": "Proteinas", "slug": "otro-slug", "description": "dup"},
        headers=admin["headers"],
    )
    assert resp.status_code == 400


def test_update_category_duplicate_slug_returns_400(client, admin, category):
    other = client.post(
        "/categories", json={"name": "Creatina", "slug": "creatina"}, headers=admin["headers"]
    ).json()

    resp = client.put(f"/categories/{other['id']}", json={"slug": "proteinas"}, headers=admin["headers"])
    assert resp.status_code == 400


def test_update_category_keeping_same_slug_is_allowed(client, admin, category):
    resp = client.put(
        f"/categories/{category['id']}", json={"description": "Actualizada"}, headers=admin["headers"]
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "Actualizada"


def test_delete_category_with_products_rejected(client, admin, category, product):
    resp = client.delete(f"/categories/{category['id']}", headers=admin["headers"])
    assert resp.status_code == 400


def test_delete_empty_category_allowed(client, admin, category):
    resp = client.delete(f"/categories/{category['id']}", headers=admin["headers"])
    assert resp.status_code == 204
