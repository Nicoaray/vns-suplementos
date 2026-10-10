"""
Script para cargar datos de ejemplo (categorias y productos de
suplementos deportivos) y un usuario administrador.

Uso (desde la carpeta backend/, con el entorno virtual activado, y
despues de aplicar las migraciones con "alembic upgrade head"):
    python -m app.seed
"""

from app.core.security import hash_password

# Importa app.db.base para que TODOS los modelos queden registrados en el
# mapper de SQLAlchemy (User.cart referencia a "Cart" como string, y
# necesita que ese modelo ya este cargado aunque este script no lo use).
from app.db.base import Base  # noqa: F401
from app.db.session import SessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.user import User, UserRole

CATEGORIES = [
    {"name": "Proteinas", "slug": "proteinas", "description": "Whey, caseina, veganas"},
    {"name": "Creatina", "slug": "creatina", "description": "Monohidrato, HCL y mas"},
    {"name": "Pre-entreno", "slug": "pre-entreno", "description": "Energia y foco para entrenar"},
    {"name": "Vitaminas", "slug": "vitaminas", "description": "Multivitaminicos y micronutrientes"},
]

PRODUCTS = [
    {"name": "Whey Protein Gold 2kg", "slug": "whey-protein-gold-2kg", "price": 45000, "stock": 30, "category_slug": "proteinas", "description": "Proteina de suero, sabor chocolate."},
    {"name": "Creatina Monohidrato 300g", "slug": "creatina-monohidrato-300g", "price": 18000, "stock": 50, "category_slug": "creatina", "description": "Creatina micronizada pura."},
    {"name": "Pre-Workout Blast 300g", "slug": "pre-workout-blast-300g", "price": 22000, "stock": 25, "category_slug": "pre-entreno", "description": "Cafeina, beta-alanina y citrulina."},
    {"name": "Multivitaminico Daily 60 caps", "slug": "multivitaminico-daily-60-caps", "price": 12000, "stock": 40, "category_slug": "vitaminas", "description": "Formula completa diaria."},
]

ADMIN_EMAIL = "admin@vns-suplementos.com"
ADMIN_PASSWORD = "CambiarEsteAdmin123!"


def run():
    db = SessionLocal()
    try:
        categories_by_slug = {}
        for cat_data in CATEGORIES:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                existing = Category(**cat_data)
                db.add(existing)
                db.flush()
            categories_by_slug[cat_data["slug"]] = existing

        for prod_data in PRODUCTS:
            slug = prod_data.pop("category_slug")
            if not db.query(Product).filter(Product.slug == prod_data["slug"]).first():
                db.add(Product(**prod_data, category_id=categories_by_slug[slug].id))

        if not db.query(User).filter(User.email == ADMIN_EMAIL).first():
            db.add(
                User(
                    email=ADMIN_EMAIL,
                    full_name="Admin VNS",
                    hashed_password=hash_password(ADMIN_PASSWORD),
                    role=UserRole.ADMIN,
                )
            )

        db.commit()
        print("Seed completo.")
        print(f"Admin -> email: {ADMIN_EMAIL} / password: {ADMIN_PASSWORD}  (cambiala despues del primer login)")
    finally:
        db.close()


if __name__ == "__main__":
    run()
