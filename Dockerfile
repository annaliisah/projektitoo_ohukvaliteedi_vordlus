FROM python:3.12-slim

WORKDIR /app

# Ainult requirements kõigepealt — Docker cache toimib hästi
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Kopeeri projekti kood
COPY scripts/ ./scripts/
COPY dashboard/ ./dashboard/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app