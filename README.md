# VNS Suplementos

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Tests](https://img.shields.io/badge/tests-63%20passing-success)
![License](https://img.shields.io/badge/license-MIT-blue)

Ecommerce de suplementos deportivos construido de punta a punta: API REST en
FastAPI, PostgreSQL con migraciones versionadas, autenticación con roles,
carrito y checkout transaccional, panel de administración y despliegue en
la nube. Pensado como **plantilla reutilizable** — la lógica de catálogo,
carrito, órdenes y autenticación es genérica y sirve de base para
cualquier otro rubro, solo cambian los datos y el branding.

**Demo en vivo:** _(agregar acá la URL una vez deployado — ver sección
[Deploy](#deploy-a-un-servidor-público-gratis))_
Nota: corre en un plan gratuito que "duerme" tras 15 min sin uso; la
primera carga puede tardar 30-50 segundos en responder.

**Usuario de prueba (admin):** `admin@vns-suplementos.com` /
`CambiarEsteAdmin123!`

## Índice

- [Funcionalidades](#funcionalidades)
- [Stack tecnológico](#stack-tecnológico)
- [Por qué este stack](#por-qué-este-stack)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Modelo de datos](#modelo-de-datos)
- [Seguridad implementada](#seguridad-implementada)
- [Cómo correrlo en local](#cómo-correrlo-en-local)
- [Tests automáticos](#tests-automáticos)
- [Probar en Postman](#probar-en-postman)
- [Deploy a un servidor público (gratis)](#deploy-a-un-servidor-público-gratis)
- [Roadmap](#roadmap)
- [Autor](#autor)

## Funcionalidades

**Cliente**
- Registro / login con JWT, catálogo paginado con búsqueda y filtros por
  categoría, precios con descuento calculados en tiempo real.
- Carrito persistente por usuario (agregar, actualizar cantidad, quitar).
- Checkout transaccional: descuenta stock y crea la orden en una sola
  transacción (nunca queda stock inconsistente si algo falla a mitad de
  camino).
- Pasarela de pago simulada (mock, con tarjetas de prueba tipo
  Stripe/MercadoPago sandbox) e historial de pedidos con estado.
- Reseñas de producto, restringidas a quien ya compró.

**Administrador**
- Panel con 5 secciones: resumen con estadísticas (ingresos, ventas por
  fecha, productos más vendidos, stock bajo), productos, categorías,
  usuarios y pedidos.
- CRUD completo de productos y categorías, con subida real de imágenes.
- Gestión de usuarios (activar/desactivar, cambiar rol) con protección
  para que un admin no pueda bloquearse a sí mismo por accidente.
- Cambio de estado de pedidos (pendiente → pagado → enviado, o cancelado).

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Base de datos | PostgreSQL 16, SQLAlchemy 2.0, Alembic (migraciones) |
| Auth | JWT (PyJWT), bcrypt, rate limiting (slowapi) |
| Frontend | HTML, CSS y JavaScript vanilla (sin build tools) |
| Infraestructura | Docker / docker-compose, Render + Neon (deploy gratuito) |
| Testing | pytest, contra una base PostgreSQL real (no mocks) |

## Por qué este stack

**Backend: FastAPI**
- Genera documentación OpenAPI/Swagger automática (`/docs`), ideal para
  probar y para importar directo a Postman.
- Tipado con Pydantic: valida cada request antes de que toque la lógica
  de negocio (menos bugs, errores 422 claros en vez de excepciones feas).
- Muy demandado en el mercado laboral junto con Spring Boot.

**Base de datos: PostgreSQL**
- Transacciones ACID reales: al confirmar una orden se descuenta stock y
  se crean los renglones de la orden en una sola transacción, sin dejar
  datos inconsistentes si algo falla a mitad de camino.
- Restricciones fuertes (FKs, `unique`, `check`) que le dan integridad
  real al modelo (usuarios, categorías, productos, carritos, órdenes).
- Es el motor por defecto en la mayoría de plataformas de deploy con capa
  gratuita, lo que simplifica la fase de publicación.

**Frontend: HTML + CSS + JavaScript vanilla**
- Sin build tools ni frameworks: se abre con un simple servidor estático
  y consume la API con `fetch`. Fácil de entender, fácil de reemplazar
  por React/Vue el día que se necesite escalarlo.

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
│   │   ├── api/routers/       endpoints (auth, categories, products, cart, orders, users, stats)
│   │   ├── main.py            arranque de la app
│   │   └── seed.py            carga de categorías/productos/admin de ejemplo
│   ├── alembic/               migraciones versionadas del esquema
│   ├── tests/                 tests automáticos (pytest)
│   ├── media/products/        imágenes de producto subidas (no versionado)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/                 catálogo, carrito, login, registro, pedidos, panel admin
├── postman/                  colección + environment listos para importar
├── docker-compose.yml        levanta Postgres + backend con un comando
├── render.yaml               blueprint de deploy (Render)
└── README.md
```

## Modelo de datos

`users` (roles `customer`/`admin`) → `carts` → `cart_items` → `products` →
`categories`. Al confirmar el carrito se crea una `order` con sus
`order_items`, se copia el precio vigente (`unit_price`) y se descuenta
stock — así una orden pasada nunca cambia de precio aunque el producto lo
haga después. `payments` registra cada intento de cobro sobre una orden.
`reviews` cuelga de `products` + `users`.

### Funcionalidades del catálogo, en detalle

- **Paginación**: `GET /products?page=1&page_size=20` devuelve
  `{ items, total, page, page_size, total_pages }` en vez de un array
  plano.
- **Descuentos**: cada producto tiene `discount_percentage` (0-90,
  validado tanto en Pydantic como con un `CHECK` en la base). El precio
  final (`final_price`) se calcula al vuelo, nunca se guarda duplicado.
- **Imágenes de producto**: `POST /products/{id}/image` (admin,
  `multipart/form-data`, campo `file`) sube una imagen real
  (JPEG/PNG/WEBP, hasta 5MB), la guarda con un nombre generado
  server-side (nunca el que manda el cliente, para evitar path
  traversal) y la sirve en `/media/products/...`.
- **Reseñas**: `POST /products/{id}/reviews` (rating 1-5 + comentario
  opcional) solo lo puede hacer quien ya compró ese producto (`403` si
  no), y como máximo una reseña por usuario y producto (`400` en la
  segunda). `GET /products/{id}` devuelve `average_rating` y
  `review_count` calculados a partir de las reseñas existentes.

## Seguridad implementada

- **Contraseñas**: hasheadas con `bcrypt` (nunca en texto plano), con
  política mínima (8+ caracteres, letra + número).
- **JWT**: firmado con `PyJWT`, algoritmo fijo (`HS256`) tanto al firmar
  como al validar — evita ataques de "confusión de algoritmo" donde un
  token manipulado fuerza `alg: none`.
- **Autorización por rol (RBAC)**: `customer` vs `admin` a nivel de cada
  endpoint (crear/editar/borrar catálogo, gestionar usuarios y ver todas
  las órdenes son exclusivos de `admin`).
- **Rate limiting**: `/auth/login` (5/min) y `/auth/register` (10/min) por
  IP, para dificultar fuerza bruta y creación masiva de cuentas.
- **Validación de entrada**: Pydantic rechaza automáticamente payloads mal
  formados (`422`) antes de que lleguen a la lógica de negocio.
- **SQL injection**: no hay SQL crudo en ningún lado — todo pasa por el
  ORM (SQLAlchemy), que parametriza las consultas.
- **CORS restringido**: solo se permiten los orígenes listados en
  `BACKEND_CORS_ORIGINS` (nunca `*` combinado con credenciales).
- **Cabeceras de seguridad** (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy`, y `Strict-Transport-Security`
  en producción).
- **`/docs` y `/redoc` ocultos en producción** (`ENVIRONMENT=production`).
- **Dependencias auditadas**: `pip-audit` sobre `requirements.txt` — cero
  vulnerabilidades conocidas al día de hoy. Se reemplazó
  `python-jose`/`passlib` (con CVEs y sin mantenimiento activo) por
  `PyJWT` y `bcrypt` directo.
- **Secretos fuera del código**: `SECRET_KEY` y credenciales de base de
  datos viven en `.env` (no versionado — ver `.gitignore`), nunca
  hardcodeados.

<details>
<summary>Pendiente / próximos pasos de seguridad (a criterio, según el uso real)</summary>

- Refresh tokens + revocación (hoy el access token expira a los 60 min y
  no se puede invalidar antes manualmente).
- Mover el JWT de `localStorage` a una cookie `httpOnly` si el frontend
  crece (reduce el riesgo de robo de token por XSS).
- HTTPS: lo resuelve la plataforma de hosting (ver [Deploy](#deploy-a-un-servidor-público-gratis))
  — nunca correr esto en producción solo con HTTP.

</details>

## Cómo correrlo en local

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

### Frontend

```bash
cd frontend
python3 -m http.server 5500
```

Abrir `http://localhost:5500`. Si el backend corre en otra URL, ajustar
`API_BASE_URL` en `frontend/js/api.js` y `BACKEND_CORS_ORIGINS` en `.env`.

<details>
<summary>Migraciones (Alembic): flujo de trabajo y un gotcha real</summary>

El esquema vive versionado en `backend/alembic/versions/`:

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

</details>

## Tests automáticos

```bash
cd backend
source .venv/bin/activate
pip install -r requirements-dev.txt

# crear una base separada solo para tests, una vez:
createdb -O vns_user vns_suplementos_test   # o el equivalente en tu gestor de Postgres

pytest -v
```

**63 tests**, contra una base de datos PostgreSQL real (no mocks) —
cada test limpia las tablas al terminar para no depender del orden de
ejecución. Cubren:

- Registro, login, validaciones y `/auth/me`.
- Catálogo público (categorías, productos, paginación, búsqueda).
- Control de acceso por rol (`401`/`403`) en categorías, productos,
  usuarios y pedidos.
- Carrito (agregar, actualizar, stock insuficiente) y checkout (crea la
  orden, descuenta stock, vacía el carrito, rechaza carrito vacío).
- Que un cliente no pueda ver pedidos ajenos.
- Descuentos y precio final; reseñas (solo quien compró, una por
  usuario, rating promedio); subida de imágenes (tipos permitidos,
  tamaño máximo).
- Gestión de usuarios: auto-protección de un admin (no puede
  desactivarse ni cambiarse el rol a sí mismo), y que un usuario
  desactivado no pueda loguearse.
- Estadísticas de administrador (resumen, ventas por fecha, productos
  más vendidos).
- Categorías/productos: rechazo de slug o nombre duplicado.
- Rate limiting de `/auth/login`.

<details>
<summary>Validado también end-to-end, a mano, contra un Postgres real</summary>

Además de la suite automática, se validó manualmente el flujo completo:
registro/login, catálogo con filtros, carrito, checkout con descuento de
stock, control de acceso por rol, migraciones con Alembic
(`upgrade`/`downgrade` de ida y vuelta, incluyendo agregar una columna
`NOT NULL` a una tabla con filas ya cargadas), reseñas (bloqueo sin
compra previa, bloqueo de duplicado) e imágenes (subida válida, rechazo
de tipo/tamaño, y que el archivo se sirve correctamente).

</details>

## Probar en Postman

1. Importar `postman/vns-suplementos.postman_collection.json` y
   `postman/vns-suplementos.postman_environment.json`.
2. Seleccionar el environment **"VNS Suplementos - Local"**.
3. Correr **Auth → Registrar cliente**, después **Auth → Login cliente**
   (guarda el token automáticamente vía script de test) y
   **Auth → Login admin** para el token de administrador.
4. Ya se puede correr el resto de las carpetas (Categories, Products,
   Cart, Orders) en orden: los IDs se van completando en el environment.

## Deploy a un servidor público (gratis)

Combinación elegida: **Render** (backend Docker + frontend estático,
gratis sin tarjeta) + **Neon** (Postgres gratis *para siempre*, sin
tarjeta, sin fecha de vencimiento — el Postgres propio de Render es
gratis pero la base se borra a los 30 días, por eso no se usa).

Con el `render.yaml` de la raíz del repo, Render crea el backend y el
frontend juntos desde "New > Blueprint". Pasos:

1. **Subir el proyecto a GitHub** (repo público o privado, da igual).
2. **Crear la base en Neon** (neon.tech, con GitHub o Google, sin
   tarjeta): "New Project" → copiar el `DATABASE_URL` que muestra (ya
   viene con `sslmode=require` incluido, no hace falta tocarlo).
3. **Crear el Blueprint en Render** (render.com, sin tarjeta): "New >
   Blueprint" → conectar el repo de GitHub → Render lee `render.yaml` y
   propone los dos servicios (`vns-suplementos-backend` y
   `vns-suplementos-frontend`).
4. Al crear el Blueprint, Render pide dos valores (marcados `sync: false`
   en el yaml, para no subirlos al repo):
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
que esté roto. Para un link que se le va a pasar a un reclutador, conviene
avisarle eso o abrir el link un rato antes.

## Roadmap

- [ ] Refresh tokens + revocación de sesión.
- [ ] Cupones / wishlist.
- [ ] Reemplazar la pasarela de pago simulada por una real (MercadoPago o
      Stripe) — la arquitectura ya está preparada para esto (patrón
      Strategy en `app/services/payments.py`).
- [ ] Migrar el frontend a React/Vue si el proyecto crece.

## Autor

**Nicolás Araya** — Técnico en Desarrollo de Software (Mendoza, Argentina)

## Licencia

Este proyecto está bajo la licencia MIT — ver [LICENSE](LICENSE).
