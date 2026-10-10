from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user, get_db
from app.crud import cart as cart_crud
from app.crud import order as crud
from app.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = cart_crud.get_or_create_cart(db, current_user)
    return crud.create_order_from_cart(db, current_user, cart, order_in)


@router.get("", response_model=list[OrderRead])
def list_my_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.list_orders_for_user(db, current_user)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = crud.get_order(db, order_id)
    if not order or (order.user_id != current_user.id and current_user.role.value != "admin"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")
    return order


@router.get("/admin/all", response_model=list[OrderRead])
def list_all_orders(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return crud.list_all_orders(db)


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    status_in: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    order = crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Orden no encontrada")
    return crud.update_order_status(db, order, status_in)
