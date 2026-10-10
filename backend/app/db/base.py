# Importa todos los modelos en un solo lugar para que
# Base.metadata.create_all() (y a futuro Alembic) los reconozca a todos.
from app.db.session import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.cart import Cart, CartItem  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.review import Review  # noqa: F401
