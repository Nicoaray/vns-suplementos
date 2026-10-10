# VNS Suplementos

Ecommerce de suplementos deportivos. Pensado como **plantilla reutilizable**:
la lógica de catálogo, carrito, órdenes y autenticación es genérica y sirve
como base para cualquier otro rubro (solo cambian los datos y el branding).

## Stack y por qué

**Backend: Python + FastAPI**
- Genera documentación OpenAPI/Swagger automática (`/docs`), ideal para probar
  y para importar directo a Postman.
- Tipado con Pydantic: valida cada request antes de que toque la lógica de
  negocio (menos bugs, errores 422 claros en vez de excepciones feas).
- Muy demandado en el mercado laboral junto con Spring Boot; alterna bien con
  tu experiencia previa en Flask, pero con menos código repetitivo.

**Base de datos: PostgreSQL**
- Transacciones ACID reales: al confirmar una orden se descuenta stock y se
  crean los renglones de la orden en una sola transacción, sin dejar datos
  inconsistentes si algo falla a mitad de camino.
- Restricciones fuertes (FKs, `unique`, `check`) que le dan integridad real
  al modelo (usuarios, categorías, productos, carritos, órdenes).
- Es el motor por defecto en la mayoría de plataformas de deploy con capa
  gratuita (Render, Railway, Neon, Fly.io), lo que simplifica la fase de
  publicación.

**Frontend: HTML + CSS + JavaScript vanilla**
- Sin build tools ni frameworks: se abre con un simple servidor estático y
  consume la API con `fetch`. Fácil de entender, fácil de reemplazar por
  React/Vue el día que quieras escalarlo.

## Estructura del proyecto

```
vns-suplementos/
├── backend/                 API en FastAPI
│   ├── app/
│   │   ├── core/            configuración, seguridad, rate limiting
│   │   ├── db/               conexión y Base de SQLAlchemy
│   │   ├── models/           tablas (SQLAlchemy)
│   │   ├── schemas/          validación de entrada/salida (Pydantic)
│   │   ├── crud/              lógica de acceso a datos
│   │   ├── api/routers/       endpoints (auth, categories, products, cart, orders)
│   │   ├── main.py            arranque de la app
│   │   └── seed.py            carga de categorías/productos/admin de ejemplo
│   ├── alembic/               migraciones versionadas del esquema
│   ├── tests/                 tests automáticos (pytest)
│   ├── media/products/        imágenes de producto subidas (no versionado)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 catálogo, carrito, login, registro, pedidos
├── postman/                  colección + environment listos para importar
├── docker-compose.yml        levanta Postgres + backend con un comando
└── README.md
```

## Modelo de datos

`users` (roles `customer`/`admin`) → `carts` → `cart_items` → `products` →
`categories`. Al confirmar el carrito se crea una `order` con sus
`order_items`, se copia el precio vigente (`unit_price`) y se descuenta
stock — así una orden pasada nunca cambia de precio aunque el producto lo
haga después. `reviews` cuelga de `products` + `users`.

## Funcionalidades del catálogo

- **Paginación**: `GET /products?page=1&page_size=20` devuelve
  `{ items, total, page, page_size, total_pages }` en vez de un array
  plano.
- **Descuentos**: cada producto tiene `discount_percentage` (0-90,
  validado tanto en Pydantic como con un `CHECK` en la base). El precio
  final (`final_price`) se calcula al vuelo, nunca se guarda duplicado.
- **Imágenes de producto**: `POST /products/{id}/image` (admin, `multipart/form-data`,
  campo `file`) sube una imagen real (JPEG/PNG/WEBP, hasta 5MB), la
  guarda con un nombre generado server-side (nunca el que manda el
  cliente, para evitar path traversal) y la sirve en `/media/products/...`.
- **Reseñas**: `POST /products/{id}/reviews` (rating 1-5 + comentario
  opcional) solo lo puede hacer quien ya compró ese producto
  (`403` si no), y como máximo una reseña por usuario y producto
  (`400` en la segunda). `GET /products/{id}` devuelve `average_rating` y
  `review_count` calculados a partir de las reseñas existentes.

## Cómo correrlo local

### Opción A: Docker (recomendada)

```bash
cp backend/.env.example backend/.env   # y generá tu propio SECRET_KEY
docker compose up --build
```

Backend en `http://localhost:8000` (docs en `/docs`), Postgres en `5432`.

El esquema de la base de datos se versiona con **Alembic** (no se crea
solo). Con el stack ya arriba, aplicar las migraciones y cargar datos de
ejemplo:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.seed
```

Admin de ejemplo: `admin@vns-suplementos.com` / `CambiarEsteAdmin123!`
(cambiala apenas puedas iniciar sesión).

### Opción B: manual (sin Docker)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ajustar DATABASE_URL a tu Postgres local
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

### Migraciones (Alembic)

El esquema vive versionado en `backend/alembic/versions/`. Flujo de trabajo:

```bash
# despues de crear/modificar un modelo en app/models/
alembic revision --autogenerate -m "descripcion del cambio"
alembic upgrade head          # aplica las migraciones pendientes
alembic downgrade -1          # revierte la ultima, si hace falta
alembic current               # ver en que revision esta la BD
```

Siempre revisar el archivo de migración generado antes de aplicarlo —
`--autogenerate` es una ayuda, no reemplaza el criterio propio (por
ejemplo, no detecta cambios de nombre de columna, los interpreta como
"borrar y crear una nueva"). Ejemplo real de este proyecto: al agregar
`discount_percentage` (columna `NOT NULL`) a una tabla `products` que ya
tenía filas, hubo que agregar a mano un `server_default='0'` a la
migración generada — si no, Postgres rechaza el `ALTER TABLE` porque las
filas existentes no tienen valor para la columna nueva (ver
`alembic/versions/b6f538079275_*.py`).

### Frontend

```bash
cd frontend
python3 -m http.server 5500
```

Abrir `http://localhost:5500`. Si el backend corre en otra URL, ajustar
`API_BASE_URL` en `frontend/js/api.js` y `BACKEND_CORS_ORIGINS` en `.env`.

## Tests automáticos

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt

# crear una base separada solo para tests, una vez:
createdb -O vns_user vns_suplementos_test   # o el equivalente en tu gestor de Postgres

pytest -v
```

36 tests cubren: registro/login/validaciones, catálogo público y paginación,
control de acceso por rol (403/401) en categorías/productos/órdenes,
carrito (agregar, actualizar, stock insuficiente), checkout (crea la
orden, descuenta stock, vacía el carrito, rechaza carrito vacío), que un
cliente no pueda ver pedidos ajenos, descuentos y precio final, subida de
imágenes (tipos permitidos, tamaño máximo, permisos), reseñas (solo quien
compró, una por usuario, rating promedio) y el rate limiting de
`/auth/login`. Corren contra una base de datos Postgres real (separada de
la de desarrollo) — no mocks — y cada test limpia las tablas al terminar
para no depender del orden de ejecución.

## Probado end-to-end

Ya validé el flujo completo corriendo el backend real contra un Postgres real
en este entorno (no son solo instrucciones sin probar):

- Registro, login, `/auth/me`.
- Catálogo público (categorías, productos, filtros, búsqueda).
- Carrito: agregar, actualizar cantidad, quitar.
- Checkout: crea la orden, descuenta stock, calcula el total.
- Control de acceso por rol: un cliente recibe `403` al intentar crear un
  producto; un admin puede.
- Sin token → `401` en endpoints protegidos.
- Validaciones (`422`) ante datos inválidos (contraseña débil, etc.).
- Migraciones con Alembic: `upgrade`/`downgrade` probados de ida y vuelta,
  incluyendo agregar una columna `NOT NULL` a una tabla con filas ya
  cargadas.
- Descuentos: `discount_percentage` aplicado, `final_price` calculado,
  rechazo de valores fuera de rango.
- Reseñas: bloqueo sin compra previa (`403`), bloqueo de reseña duplicada
  (`400`), `average_rating`/`review_count` actualizados.
- Imágenes: subida válida (JPEG/PNG/WEBP), rechazo de tipo no permitido y
  de archivo mayor a 5MB, y que el archivo subido se sirve correctamente
  en `/media/products/...`.

## Probar en Postman

1. Importar `postman/vns-suplementos.postman_collection.json` y
   `postman/vns-suplementos.postman_environment.json`.
2. Seleccionar el environment **"VNS Suplementos - Local"**.
3. Correr **Auth → Registrar cliente**, después **Auth → Login cliente**
   (guarda el token solo automáticamente vía script de test) y
   **Auth → Login admin** para el token de administrador.
4. Ya podés correr el resto de las carpetas (Categories, Products, Cart,
   Orders) en orden: los IDs se van completando en el environment.

## Seguridad implementada

- **Contraseñas**: hasheadas con `bcrypt` (nunca en texto plano), con
  política mínima (8+ caracteres, letra + número).
- **JWT**: firmado con `PyJWT`, algoritmo fijo (`HS256`) tanto al firmar
  como al validar — evita ataques de "confusión de algoritmo" donde un
  token manipulado fuerza `alg: none`.
- **Autorización por rol (RBAC)**: `customer` vs `admin` a nivel de cada
  endpoint (crear/editar/borrar catálogo y ver todas las órdenes son
  exclusivos de `admin`).
- **Rate limiting**: `/auth/login` (5/min) y `/auth/register` (10/min) por
  IP, para dificultar fuerza bruta y creación masiva de cuentas.
- **Validación de entrada**: Pydantic rechaza automáticamente payloads mal
  formados (`422`) antes de que lleguen a la lógica de negocio.
- **SQL injection**: no hay SQL crudo en ningún lado — todo pasa por el ORM
  (SQLAlchemy), que parametriza las consultas.
- **CORS restringido**: solo se permiten los orígenes listados en
  `BACKEND_CORS_ORIGINS` (nunca `*` combinado con credenciales).
- **Cabeceras de seguridad** (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`, y `Strict-Transport-Security` en
  producción).
- **`/docs` y `/redoc` ocultos en producción** (`ENVIRONMENT=production`).
- **Dependencias auditadas**: corrí `pip-audit` sobre `requirements.txt` —
  cero vulnerabilidades conocidas al día de hoy. Se reemplazó
  `python-jose`/`passlib` (con CVEs y sin mantenimiento activo) por
  `PyJWT` y `bcrypt` directo.
- **Secretos fuera del código**: `SECRET_KEY` y credenciales de base de
  datos viven en `.env` (no versionado — ver `.gitignore`), nunca
  hardcodeados.

### Pendiente / próximos pasos de seguridad (a criterio, según el uso real)

- Refresh tokens + revocación (hoy el access token expira a los 60 min y
  no se puede invalidar antes manualmente).
- Mover el JWT de `localStorage` a una cookie `httpOnly` si el frontend
  crece (reduce el riesgo de robo de token por XSS).
- Migraciones versionadas con Alembic en vez de `create_all()` (necesario
  antes de tener datos reales en producción).
- HTTPS: lo resuelve la plataforma de hosting (ver deploy) — Nunca correr
  esto en producción solo con HTTP.

## Deploy a un servidor público (gratis)

Combinación elegida: **Render** (backend Docker + frontend estático,
gratis sin tarjeta) + **Neon** (Postgres gratis *para siempre*, sin
tarjeta, sin fecha de vencimiento — el Postgres propio de Render es
gratis pero la base se borra a los 30 días, por eso no se usa).

Con el `render.yaml` de la raíz del repo, Render crea el backend y el
frontend juntos desde "New > Blueprint". Pasos:

1. **Subir el proyecto a GitHub** (repo público o privado, da igual).
2. **Crear la base en Neon** (neon.tech, con GitHub o Google, sin
   tarjeta): "New Project" → copiar el `DATABASE_URL` que te muestra
   (ya viene con `sslmode=require` incluido, no hace falta tocarlo).
3. **Crear el Blueprint en Render** (render.com, sin tarjeta): "New >
   Blueprint" → conectar el repo de GitHub → Render lee `render.yaml` y
   propone los dos servicios (`vns-suplementos-backend` y
   `vns-suplementos-frontend`).
4. Al crear el Blueprint, Render va a pedir dos valores (los que quedaron
   marcados `sync: false` en el yaml, para no subirlos al repo):
   - `DATABASE_URL`: pegar el que copiaste de Neon.
   - `BACKEND_CORS_ORIGINS`: dejarlo vacío por ahora, se completa en el
     paso 6.
5. Esperar el primer deploy de ambos servicios (unos minutos). Copiar la
   URL pública que Render le asigna al backend (arriba a la izquierda en
   el dashboard del servicio, termina en `.onrender.com`).
6. **Conectar frontend y backend:**
   - En `frontend/js/api.js`, reemplazar
     `https://vns-suplementos-backend.onrender.com` por la URL real del
     paso 5 (si coincide, no hace falta tocar nada), subir el cambio a
     GitHub — Render redeploya el frontend solo.
   - En el servicio del backend en Render, editar la variable
     `BACKEND_CORS_ORIGINS` con la URL real del frontend (la de
     `vns-suplementos-frontend`, también `.onrender.com`) y guardar —
     Render redeploya el backend solo.
7. **Cargar datos de arranque**: en el dashboard del backend en Render,
   pestaña "Shell", correr `python -m app.seed` una sola vez.

Importante para la demo: el backend gratis de Render "se duerme" después
de 15 minutos sin tráfico, y la primera visita después de eso tarda
30-50 segundos en responder mientras arranca de nuevo — es normal, no es
que esté roto. Para un link que le vas a pasar a un reclutador, avisale
eso o abrí el link vos un rato antes.

Si en el futuro se necesita algo que no duerma nunca (o más almacenamiento
en Neon), ahí sí hay que pasar a un plan pago — pero para probarlo y
mostrarlo en el portfolio, esta combinación no vence ni pide tarjeta.
