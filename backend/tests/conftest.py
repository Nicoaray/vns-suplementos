import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Base de datos separada para tests: nunca corren contra la base de
# desarrollo/produccion. Se puede sobreescribir con la variable de
# entorno TEST_DATABASE_URL (por ejemplo en CI).
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://vns_user:vns_password@localhost:5432/vns_suplementos_test",
)

from app.core.limiter import limiter  # noqa: E402
from app.db.base import Base  # noqa: E402

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def _disable_rate_limiter_by_default():
    # El rate limiting se prueba de forma explicita en
    # test_rate_limiting.py, que lo reactiva puntualmente. En el resto de
    # los tests lo dejamos apagado para que no interfiera entre si.
    limiter.enabled = False
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    with test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(text(f'TRUNCATE TABLE "{table.name}" RESTART IDENTITY CASCADE'))


@pytest.fixture
def client():
    from app.api.deps import get_db
    from app.main import app

    def _override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def customer(client):
    payload = {"email": "cliente@test.com", "full_name": "Cliente Test", "password": "Segura123"}
    client.post("/auth/register", json=payload)
    token = client.post(
        "/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    ).json()["access_token"]
    return {"email": payload["email"], "token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def admin(client):
    # No existe (a proposito) un endpoint publico para crear admins: se
    # inserta directo en la base, igual que haria un seed/superusuario.
    from app.core.security import hash_password
    from app.models.user import User, UserRole

    db = TestSessionLocal()
    db.add(
        User(
            email="admin@test.com",
            full_name="Admin Test",
            hashed_password=hash_password("AdminSegura123"),
            role=UserRole.ADMIN,
        )
    )
    db.commit()
    db.close()

    token = client.post(
        "/auth/login",
        data={"username": "admin@test.com", "password": "AdminSegura123"},
    ).json()["access_token"]
    return {"token": token, "headers": {"Authorization": f"Bearer {token}"}}


@pytest.fixture
def category(client, admin):
    resp = client.post(
        "/categories",
        json={"name": "Proteinas", "slug": "proteinas", "description": "Test"},
        headers=admin["headers"],
    )
    return resp.json()


@pytest.fixture
def product(client, admin, category):
    resp = client.post(
        "/products",
        json={
            "name": "Whey Test",
            "slug": "whey-test",
            "price": 10000,
            "stock": 5,
            "category_id": category["id"],
        },
        headers=admin["headers"],
    )
    return resp.json()
