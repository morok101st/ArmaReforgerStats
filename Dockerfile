# ---- Dockerfile ----

# 1) Basisimage mit Python
FROM python:3.9-slim

# 2) Verzeichnis für unseren Code
WORKDIR /app

# 3) Benötigte Python-Packages (Flask)
RUN pip install flask

# 4) Kopiere den Quellcode ins Image
COPY main.py /app/main.py

# 5) Falls du das Log-Verzeichnis oder offset-Datei persistent halten willst, machst du ein Volume:
# VOLUME /app/logs

# 6) Flask hört auf 8880 (Prometheus ruft http://container:8880/metrics ab)
EXPOSE 8880

# 7) Starte main.py
CMD ["python", "/app/main.py"]
