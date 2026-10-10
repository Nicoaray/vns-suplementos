from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import cart as crud
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartRead

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartRead)
def read_cart(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return crud.get_or_create_cart(db, current_user)


@router.post("/items", response_model=CartRead)
def add_item(
    item_in: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = crud.get_or_create_cart(db, current_user)
    return crud.add_item(db, cart, item_in)


@router.put("/items/{item_id}", response_model=CartRead)
def update_item(
    item_id: int,
    item_in: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = crud.get_or_create_cart(db, current_user)
    return crud.update_item(db, cart, item_id, item_in)


@router.delete("/items/{item_id}", response_model=CartRead)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cart = crud.get_or_create_cart(db, current_user)
    return crud.remove_item(db, cart, item_id)
