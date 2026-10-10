import pytest

from app.core.limiter import limiter


@pytest.fixture(autouse=True)
def _enable_limiter_for_this_module():
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.enabled = False


def test_login_is_rate_limited_after_five_attempts_per_minute(client):
    client.post(
        "/auth/register",
        json={"email": "ratelimit@test.com", "full_name": "RL", "password": "Segura123"},
    )

    statuses = []
    for _ in range(6):
        resp = client.post(
            "/auth/login",
            data={"username": "ratelimit@test.com", "password": "incorrecta"},
        )
        statuses.append(resp.status_code)

    # Las primeras 5 fallan por credenciales invalidas (401); la 6ta cae
    # en el limite de 5/minuto y responde 429 antes de tocar la logica de
    # autenticacion.
    assert statuses[:5] == [401, 401, 401, 401, 401]
    assert statuses[5] == 429
