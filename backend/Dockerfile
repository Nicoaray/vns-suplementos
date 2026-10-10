FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema para compilar psycopg2 si hiciera falta
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Render (y plataformas similares) inyectan la variable PORT y esperan
# que la app escuche ahi; en local (docker-compose) no esta seteada,
# entonces usa 8000 por defecto.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
