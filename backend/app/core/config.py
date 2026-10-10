from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ (carpeta que contiene app/, no depende del cwd desde donde se
# arranque uvicorn/pytest).
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Configuracion central de la app. Los valores se leen de variables de
    entorno (o de un archivo .env en desarrollo). Nunca hardcodear
    credenciales o secretos aca.
    """

    PROJECT_NAME: str = "VNS Suplementos API"

    DATABASE_URL: str = "postgresql://vns_user:vns_password@localhost:5432/vns_suplementos"

    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    BACKEND_CORS_ORIGINS: str = "http://localhost:5500,http://127.0.0.1:5500"

    # "development" muestra /docs y /redoc; "production" los oculta para
    # no exponer el mapa completo de la API a cualquiera que lo visite.
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def media_root(self) -> Path:
        return BASE_DIR / "media"


settings = Settings()
