# Dockerfile für Immotop Invoice Classifier Backend
# Mit libzbar für Swiss QR-Code Erkennung

FROM python:3.11-slim

# System-Dependencies für QR-Code Erkennung
RUN apt-get update && apt-get install -y \
    libzbar0 \
    libzbar-dev \
    && rm -rf /var/lib/apt/lists/*

# Arbeitsverzeichnis
WORKDIR /app

# Requirements zuerst (für besseres Caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Port von Umgebungsvariable (Render setzt $PORT)
ENV PORT=8000

# Gunicorn mit Uvicorn Worker starten
CMD gunicorn --bind=0.0.0.0:$PORT --workers=1 --timeout=120 application:application -k uvicorn.workers.UvicornWorker
