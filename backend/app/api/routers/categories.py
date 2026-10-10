from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.crud import category as crud
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return crud.list_categories(db)


@router.get("/{category_id}", response_model=CategoryRead)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria no encontrada")
    return category


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    if crud.get_category_by_slug(db, category_in.slug):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe una categoria con ese slug")
    if crud.get_category_by_name(db, category_in.name):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe una categoria con ese nombre")
    return crud.create_category(db, category_in)

@router.put("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria no encontrada")

    if category_in.slug is not None:
        other = crud.get_category_by_slug(db, category_in.slug)
        if other and other.id != category_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe una categoria con ese slug")
    if category_in.name is not None:
        other = crud.get_category_by_name(db, category_in.name)
        if other and other.id != category_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe una categoria con ese nombre")

    return crud.update_category(db, category, category_in)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = crud.get_category(db, category_id)
    if not category:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Categoria no encontrada")
    if crud.has_products(db, category_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "No se puede borrar: tiene productos asociados. Movelos a otra categoria primero.",
        )
    crud.delete_category(db, category)
