import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole

# Al menos una letra y un numero, largo entre 8 y 128 (ver Field abajo).
_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).+$")


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, value: str) -> str:
        if not _PASSWORD_RE.match(value):
            raise ValueError("La contraseña debe tener al menos una letra y un número")
        return value


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class UserAdminUpdate(BaseModel):
    """Lo unico que un admin puede cambiarle a otro usuario: su rol y si
    esta activo. Nunca el email/password de otra persona."""
    role: UserRole | None = None
    is_active: bool | None = None
