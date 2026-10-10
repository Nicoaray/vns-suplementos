from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.review import Review
from app.schemas.product import ProductCreate, ProductUpdate


def get_product_by_slug(db: Session, slug: str) -> Product | None:
    return db.query(Product).filter(Product.slug == slug).first()


def _attach_rating_stats(db: Session, products: list[Product]) -> list[Product]:
    """Adjunta average_rating/review_count a cada producto (no son
    columnas de la tabla: se calculan al vuelo con una sola query
    agregada, en vez de una consulta de reviews por producto)."""
    if not products:
        return products

    ids = [p.id for p in products]
    rows = (
        db.query(Review.product_id, func.avg(Review.rating), func.count(Review.id))
        .filter(Review.product_id.in_(ids))
        .group_by(Review.product_id)
        .all()
    )
    stats = {product_id: (float(avg), count) for product_id, avg, count in rows}

    for product in products:
        avg, count = stats.get(product.id, (None, 0))
        product.average_rating = round(avg, 2) if avg is not None else None
        product.review_count = count

    return products


def get_product(db: Session, product_id: int) -> Product | None:
    product = db.get(Product, product_id)
    if product:
        _attach_rating_stats(db, [product])
    return product


def list_products(
    db: Session,
    category_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Product], int]:
    query = db.query(Product).filter(Product.is_active.is_(True))
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    total = query.count()
    items = query.order_by(Product.id).offset((page - 1) * page_size).limit(page_size).all()
    _attach_rating_stats(db, items)
    return items, total


def list_new_arrivals(db: Session, limit: int = 10) -> list[Product]:
    """Productos "nuevos": los cargados mas recientemente."""
    items = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .order_by(Product.created_at.desc())
        .limit(limit)
        .all()
    )
    return _attach_rating_stats(db, items)


def list_on_sale(db: Session, limit: int = 10) -> list[Product]:
    """Productos con descuento activo, del mas descontado al menos."""
    items = (
        db.query(Product)
        .filter(Product.is_active.is_(True), Product.discount_percentage > 0)
        .order_by(Product.discount_percentage.desc())
        .limit(limit)
        .all()
    )
    return _attach_rating_stats(db, items)


def list_featured(db: Session, limit: int = 10) -> list[Product]:
    """Productos "destacados": los mas vendidos por unidades, contando
    solo ordenes pagadas o enviadas (una compra simulada/cancelada no
    cuenta). Si todavia no hay ventas suficientes -proyecto recien
    instalado, sin pedidos pagados-, se completa con los mas nuevos
    para que el carrusel nunca quede vacio."""
    sold = (
        db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label("qty"))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status.in_([OrderStatus.PAID, OrderStatus.SHIPPED]))
        .group_by(OrderItem.product_id)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    product_ids = [row.product_id for row in sold]

    items: list[Product] = []
    if product_ids:
        by_id = {
            p.id: p
            for p in db.query(Product).filter(Product.id.in_(product_ids), Product.is_active.is_(True)).all()
        }
        items = [by_id[pid] for pid in product_ids if pid in by_id]

    if len(items) < limit:
        existing_ids = [p.id for p in items]
        extra_query = db.query(Product).filter(Product.is_active.is_(True))
        if existing_ids:
            extra_query = extra_query.filter(Product.id.notin_(existing_ids))
        extra = extra_query.order_by(Product.created_at.desc()).limit(limit - len(items)).all()
        items.extend(extra)

    return _attach_rating_stats(db, items)


def list_all_for_admin(db: Session) -> list[Product]:
    """Todos los productos, activos e inactivos (borrado logico
    incluido), para el panel de administracion."""
    items = db.query(Product).order_by(Product.id).all()
    return _attach_rating_stats(db, items)


def create_product(db: Session, product_in: ProductCreate) -> Product:
    product = Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    _attach_rating_stats(db, [product])
    return product


def update_product(db: Session, product: Product, product_in: ProductUpdate) -> Product:
    for field, value in product_in.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    _attach_rating_stats(db, [product])
    return product


def delete_product(db: Session, product: Product) -> None:
    # Baja logica en vez de borrado fisico: conserva el historial en
    # ordenes pasadas que referencian este producto.
    product.is_active = False
    db.commit()
