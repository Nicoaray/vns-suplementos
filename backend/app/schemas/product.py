from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryRead


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    slug: str = Field(min_length=2, max_length=220)
    description: str | None = Field(default=None, max_length=2000)
    price: float = Field(gt=0)
    discount_percentage: int = Field(default=0, ge=0, le=90)
    stock: int = Field(ge=0)
    image_url: str | None = None
    category_id: int


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    price: float | None = Field(default=None, gt=0)
    discount_percentage: int | None = Field(default=None, ge=0, le=90)
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    category_id: int | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    description: str | None
    price: float
    discount_percentage: int
    final_price: float
    stock: int
    image_url: str | None
    is_active: bool
    category: CategoryRead
    average_rating: float | None = None
    review_count: int = 0


class ProductListRead(BaseModel):
    items: list[ProductRead]
    total: int
    page: int
    page_size: int
    total_pages: int
