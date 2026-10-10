from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate


def get_or_create_cart(db: Session, user: User) -> Cart:
    if user.cart:
        return user.cart
    cart = Cart(user_id=user.id)
    db.add(cart)
    db.commit()
    db.refresh(cart)
    return cart


def add_item(db: Session, cart: Cart, item_in: CartItemCreate) -> Cart:
    product = db.get(Product, item_in.product_id)
    if not product or not product.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    if item_in.quantity > product.stock:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stock insuficiente")

    existing = next((i for i in cart.items if i.product_id == item_in.product_id), None)
    if existing:
        existing.quantity += item_in.quantity
    else:
        db.add(CartItem(cart_id=cart.id, product_id=item_in.product_id, quantity=item_in.quantity))

    db.commit()
    db.refresh(cart)
    return cart


def update_item(db: Session, cart: Cart, item_id: int, item_in: CartItemUpdate) -> Cart:
    item = next((i for i in cart.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item no encontrado en el carrito")
    if item_in.quantity > item.product.stock:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Stock insuficiente")
    item.quantity = item_in.quantity
    db.commit()
    db.refresh(cart)
    return cart


def remove_item(db: Session, cart: Cart, item_id: int) -> Cart:
    item = next((i for i in cart.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item no encontrado en el carrito")
    db.delete(item)
    db.commit()
    db.refresh(cart)
    return cart
