from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductRead


class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantity: int
    product: ProductRead


class CartRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    items: list[CartItemRead]
