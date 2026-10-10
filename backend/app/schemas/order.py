from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.order import OrderStatus
from app.schemas.product import ProductRead
from app.schemas.user import UserRead


class OrderCreate(BaseModel):
    shipping_address: str = Field(min_length=5, max_length=500)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantity: int
    unit_price: float
    product: ProductRead


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    total_amount: float
    shipping_address: str
    created_at: datetime
    items: list[OrderItemRead]
    # Solo tiene sentido para el admin (que ve pedidos de todos), pero no
    # hace mal mostrarselo tambien al propio cliente en sus pedidos.
    user: UserRead


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
