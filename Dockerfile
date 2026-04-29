# ── SnapIT — Dockerfile de producción ────────────────────────────────────────
# Imagen base: Python 3.11 slim (estable, compatible con todas las dependencias)
FROM python:3.11-slim

# Dependencias del sistema para OpenCV / PIL / ultralytics
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxrender1 libxext6 git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python primero (aprovecha caché de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Puerto por defecto; Railway sobreescribe con $PORT
EXPOSE 8000

# Producción: sin --reload, workers según CPUs disponibles
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
