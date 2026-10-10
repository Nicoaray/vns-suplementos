from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.schemas.order import OrderCreate, OrderStatusUpdate


def create_order_from_cart(db: Session, user: User, cart: Cart, order_in: OrderCreate) -> Order:
    if not cart.items:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El carrito esta vacio")

    for item in cart.items:
        if item.quantity > item.product.stock:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Stock insuficiente para '{item.product.name}'",
            )

    total = sum(item.quantity * float(item.product.price) for item in cart.items)

    order = Order(
        user_id=user.id,
        total_amount=total,
        shipping_address=order_in.shipping_address,
        status=OrderStatus.PENDING,
    )
    db.add(order)
    db.flush()  # asigna order.id sin cerrar la transaccion todavia

    for item in cart.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.product.price,
            )
        )
        # Descuenta stock. En un caso real de alta concurrencia esto
        # deberia hacerse con un UPDATE atomico o un lock; para el MVP
        # alcanza con esto dentro de la misma transaccion.
        item.product.stock -= item.quantity

    for item in list(cart.items):
        db.delete(item)

    db.commit()
    db.refresh(order)
    return order


def list_orders_for_user(db: Session, user: User) -> list[Order]:
    return db.query(Order).filter(Order.user_id == user.id).order_by(Order.created_at.desc()).all()


def list_all_orders(db: Session) -> list[Order]:
    return db.query(Order).order_by(Order.created_at.desc()).all()


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def update_order_status(db: Session, order: Order, status_in: OrderStatusUpdate) -> Order:
    order.status = status_in.status
    db.commit()
    db.refresh(order)
    return order
