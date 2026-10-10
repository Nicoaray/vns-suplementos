def _buy_product(client, customer, product, quantity=1):
    client.post(
        "/cart/items",
        json={"product_id": product["id"], "quantity": quantity},
        headers=customer["headers"],
    )
    return client.post(
        "/orders", json={"shipping_address": "Test 123"}, headers=customer["headers"]
    )


def test_cannot_review_without_purchasing(client, customer, product):
    resp = client.post(
        f"/products/{product['id']}/reviews",
        json={"rating": 5, "comment": "Genial"},
        headers=customer["headers"],
    )
    assert resp.status_code == 403


def test_can_review_after_purchasing(client, customer, product):
    _buy_product(client, customer, product)

    resp = client.post(
        f"/products/{product['id']}/reviews",
        json={"rating": 4, "comment": "Muy bueno"},
        headers=customer["headers"],
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["rating"] == 4
    assert body["user"]["full_name"] == "Cliente Test"

    listing = client.get(f"/products/{product['id']}/reviews")
    assert len(listing.json()) == 1


def test_cannot_review_same_product_twice(client, customer, product):
    _buy_product(client, customer, product)
    client.post(
        f"/products/{product['id']}/reviews", json={"rating": 5}, headers=customer["headers"]
    )
    resp = client.post(
        f"/products/{product['id']}/reviews", json={"rating": 3}, headers=customer["headers"]
    )
    assert resp.status_code == 400


def test_review_rating_out_of_range_rejected(client, customer, product):
    _buy_product(client, customer, product)
    resp = client.post(
        f"/products/{product['id']}/reviews", json={"rating": 0}, headers=customer["headers"]
    )
    assert resp.status_code == 422


def test_product_shows_average_rating_after_review(client, customer, product):
    _buy_product(client, customer, product)
    client.post(
        f"/products/{product['id']}/reviews", json={"rating": 4}, headers=customer["headers"]
    )

    resp = client.get(f"/products/{product['id']}")
    body = resp.json()
    assert body["average_rating"] == 4.0
    assert body["review_count"] == 1


def test_review_requires_auth(client, product):
    resp = client.post(f"/products/{product['id']}/reviews", json={"rating": 5})
    assert resp.status_code == 401
