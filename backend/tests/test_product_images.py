import base64
import io

import pytest

from app.core.config import settings

# PNG 1x1 valido (el mismo que se uso para probar esto manualmente).
_TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@pytest.fixture(autouse=True)
def _use_tmp_media_root(tmp_path, monkeypatch):
    # Los tests de imagenes escriben archivos reales: se redirige
    # media_root a un directorio temporal para no ensuciar backend/media.
    monkeypatch.setattr(type(settings), "media_root", property(lambda self: tmp_path))
    yield


def test_customer_cannot_upload_image(client, customer, product):
    files = {"file": ("pixel.png", io.BytesIO(_TINY_PNG), "image/png")}
    resp = client.post(f"/products/{product['id']}/image", headers=customer["headers"], files=files)
    assert resp.status_code == 403


def test_admin_uploads_valid_image(client, admin, product):
    files = {"file": ("pixel.png", io.BytesIO(_TINY_PNG), "image/png")}
    resp = client.post(f"/products/{product['id']}/image", headers=admin["headers"], files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["image_url"].startswith("/media/products/")
    assert body["image_url"].endswith(".png")


def test_rejects_disallowed_content_type(client, admin, product):
    files = {"file": ("nota.txt", io.BytesIO(b"no es una imagen"), "text/plain")}
    resp = client.post(f"/products/{product['id']}/image", headers=admin["headers"], files=files)
    assert resp.status_code == 400


def test_rejects_oversized_image(client, admin, product):
    big_content = b"0" * (5 * 1024 * 1024 + 1)
    files = {"file": ("grande.png", io.BytesIO(big_content), "image/png")}
    resp = client.post(f"/products/{product['id']}/image", headers=admin["headers"], files=files)
    assert resp.status_code == 400


def test_image_upload_for_missing_product_returns_404(client, admin):
    files = {"file": ("pixel.png", io.BytesIO(_TINY_PNG), "image/png")}
    resp = client.post("/products/9999/image", headers=admin["headers"], files=files)
    assert resp.status_code == 404
