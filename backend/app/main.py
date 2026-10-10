from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routers import auth, cart, categories, orders, products, stats, users
from app.core.config import settings
from app.core.limiter import limiter

# En production ocultamos /docs y /redoc para no exponer el mapa completo
# de la API a cualquiera que la visite (security through... menos
# superficie de ataque, no es la unica proteccion pero suma).
docs_url = "/docs" if settings.ENVIRONMENT != "production" else None
redoc_url = "/redoc" if settings.ENVIRONMENT != "production" else None
openapi_url = "/openapi.json" if settings.ENVIRONMENT != "production" else None

app = FastAPI(title=settings.PROJECT_NAME, docs_url=docs_url, redoc_url=redoc_url, openapi_url=openapi_url)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS: solo se permiten los origenes configurados en .env. En produccion
# BACKEND_CORS_ORIGINS debe listar unicamente el dominio real del
# frontend (nunca "*" combinado con allow_credentials=True).
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Cabeceras basicas recomendadas por OWASP Secure Headers Project.
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.ENVIRONMENT == "production":
        # Solo tiene sentido si el sitio se sirve por HTTPS (lo hace el
        # proveedor de hosting/proxy en la fase de deploy).
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(stats.router)

# Sirve las imagenes de producto subidas via POST /products/{id}/image.
# En produccion, si el volumen de trafico lo justifica, esto conviene
# moverlo a un bucket (S3/Cloud Storage) + CDN en vez de servirlo desde
# el propio backend.
settings.media_root.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(settings.media_root)), name="media")


# El esquema de la base de datos ya no se crea automaticamente al
# arrancar: se versiona con Alembic. Antes de levantar la app por primera
# vez (o despues de tocar un modelo), correr:
#   alembic upgrade head


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
