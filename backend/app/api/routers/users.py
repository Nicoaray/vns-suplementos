from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.crud import user as crud
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return crud.list_users(db)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado")

    # Un admin no puede desactivarse ni quitarse el rol a si mismo: evita
    # que la cuenta administradora quede bloqueada sin nadie que pueda
    # revertirlo.
    if user.id == admin.id:
        if data.is_active is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No podes desactivar tu propia cuenta")
        if data.role is not None and data.role != admin.role:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "No podes cambiar tu propio rol")

    return crud.update_user_admin(db, user, data)
