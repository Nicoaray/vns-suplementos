from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.crud import stats as crud
from app.models.user import User
from app.schemas.stats import SalesByDate, SummaryStats, TopProduct

router = APIRouter(prefix="/admin/stats", tags=["admin-stats"])


@router.get("/summary", response_model=SummaryStats)
def summary(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return crud.get_summary(db)


@router.get("/sales-by-date", response_model=list[SalesByDate])
def sales_by_date(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return crud.get_sales_by_date(db)


@router.get("/top-products", response_model=list[TopProduct])
def top_products(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return crud.get_top_products(db, limit=limit)
