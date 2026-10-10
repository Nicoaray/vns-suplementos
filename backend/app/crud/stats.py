from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.order import Order, OrderItem, OrderStatus
from app.models.product import Product
from app.models.user import User

# Un producto con este stock o menos se considera "poco stock" en el
# resumen del panel de administracion.
LOW_STOCK_THRESHOLD = 5

# Estados que representan una venta real (para ingresos/estadisticas).
# "pending" todavia no se cobro y "cancelled" nunca se cobro: ninguno de
# los dos cuenta como ingreso.
SOLD_STATUSES = [OrderStatus.PAID, OrderStatus.SHIPPED]


def get_summary(db: Session) -> dict:
    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0))
        .filter(Order.status.in_(SOLD_STATUSES))
        .scalar()
    )

    orders_by_status = dict(
        db.query(Order.status, func.count(Order.id)).group_by(Order.status).all()
    )

    return {
        "total_revenue": float(total_revenue or 0),
        "total_orders": sum(orders_by_status.values()),
        "pending_orders": orders_by_status.get(OrderStatus.PENDING, 0),
        "paid_orders": orders_by_status.get(OrderStatus.PAID, 0),
        "shipped_orders": orders_by_status.get(OrderStatus.SHIPPED, 0),
        "cancelled_orders": orders_by_status.get(OrderStatus.CANCELLED, 0),
        "total_customers": db.query(func.count(User.id)).scalar() or 0,
        "active_products": db.query(func.count(Product.id)).filter(Product.is_active.is_(True)).scalar() or 0,
        "low_stock_products": (
            db.query(func.count(Product.id))
            .filter(Product.is_active.is_(True), Product.stock <= LOW_STOCK_THRESHOLD)
            .scalar()
            or 0
        ),
    }


def get_sales_by_date(db: Session) -> list[dict]:
    day = func.date(Order.created_at)
    rows = (
        db.query(day.label("day"), func.sum(Order.total_amount).label("revenue"), func.count(Order.id).label("orders_count"))
        .filter(Order.status.in_(SOLD_STATUSES))
        .group_by(day)
        .order_by(day)
        .all()
    )
    return [
        {"day": row.day, "revenue": float(row.revenue or 0), "orders_count": row.orders_count}
        for row in rows
    ]


def get_top_products(db: Session, limit: int = 10) -> list[dict]:
    rows = (
        db.query(
            Product.id.label("product_id"),
            Product.name.label("name"),
            func.sum(OrderItem.quantity).label("quantity_sold"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.status.in_(SOLD_STATUSES))
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "product_id": row.product_id,
            "name": row.name,
            "quantity_sold": int(row.quantity_sold or 0),
            "revenue": float(row.revenue or 0),
        }
        for row in rows
    ]
