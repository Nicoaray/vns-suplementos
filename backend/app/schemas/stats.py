from datetime import date

from pydantic import BaseModel


class SummaryStats(BaseModel):
    total_revenue: float
    total_orders: int
    pending_orders: int
    paid_orders: int
    shipped_orders: int
    cancelled_orders: int
    total_customers: int
    active_products: int
    low_stock_products: int


class SalesByDate(BaseModel):
    day: date
    revenue: float
    orders_count: int


class TopProduct(BaseModel):
    product_id: int
    name: str
    quantity_sold: int
    revenue: float
