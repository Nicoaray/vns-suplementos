import math
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_current_user, get_db
from app.core.config import settings
from app.crud import product as crud
from app.crud import review as review_crud
from app.models.user import User
from app.schemas.product import ProductCreate, ProductListRead, ProductRead, ProductUpdate
from app.schemas.review import ReviewCreate, ReviewRead

router = APIRouter(prefix="/products", tags=["products"])

# Solo estos tipos de imagen se aceptan, y se valida por el contenido real
# que reporta el cliente (Content-Type), no por la extension del nombre
# de archivo (que el usuario podria falsear).
ALLOWED_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5MB


@router.get("", response_model=ProductListRead)
def list_products(
    category_id: int | None = None,
    search: str | None = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = crud.list_products(db, category_id=category_id, search=search, page=page, page_size=page_size)
    total_pages = math.ceil(total / page_size) if total else 0
    return ProductListRead(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.get("/featured", response_model=list[ProductRead])
def list_featured_products(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    return crud.list_featured(db, limit=limit)


@router.get("/new", response_model=list[ProductRead])
def list_new_products(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    return crud.list_new_arrivals(db, limit=limit)


@router.get("/on-sale", response_model=list[ProductRead])
def list_on_sale_products(limit: int = Query(default=10, ge=1, le=50), db: Session = Depends(get_db)):
    return crud.list_on_sale(db, limit=limit)


@router.get("/admin/all", response_model=list[ProductRead])
def list_all_products_admin(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return crud.list_all_for_admin(db)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product or not product.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return product


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    if crud.get_product_by_slug(db, product_in.slug):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya existe un producto con ese slug")
    return crud.create_product(db, product_in)

@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return crud.update_product(db, product, product_in)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    crud.delete_product(db, product)


@router.post("/{product_id}/image", response_model=ProductRead)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")

    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Formato no permitido (usar JPEG, PNG o WEBP)")

    # Se lee un byte de mas que el limite para detectar excedidos sin
    # tener que cargar archivos gigantes enteros en memoria.
    contents = await file.read(MAX_IMAGE_BYTES + 1)
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La imagen supera el tamaño máximo (5MB)")
    if not contents:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Archivo vacío")

    products_dir = settings.media_root / "products"
    products_dir.mkdir(parents=True, exist_ok=True)

    # El nombre de archivo nunca sale del cliente: se genera server-side
    # para evitar path traversal (ej. "../../etc/passwd") o que un
    # usuario pise el archivo de otro producto.
    filename = f"{uuid.uuid4().hex}{ALLOWED_IMAGE_TYPES[file.content_type]}"
    (products_dir / filename).write_bytes(contents)

    product.image_url = f"/media/products/{filename}"
    db.commit()
    db.refresh(product)
    return crud.get_product(db, product_id)


@router.get("/{product_id}/reviews", response_model=list[ReviewRead])
def list_product_reviews(product_id: int, db: Session = Depends(get_db)):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")
    return review_crud.list_reviews_for_product(db, product_id)


@router.post("/{product_id}/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_product_review(
    product_id: int,
    review_in: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Producto no encontrado")

    if not review_crud.user_has_purchased(db, current_user, product_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Solo se puede reseñar un producto que ya compraste",
        )
    if review_crud.user_already_reviewed(db, current_user, product_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ya dejaste una reseña para este producto")

    return review_crud.create_review(db, current_user, product_id, review_in)
