# Horizon - Dockerfile - owned by Dev 3 (AI + Infra)
#
# Builds backend + ai together into a single production image.
# frontend/ is NOT in this image — it deploys to Vercel separately.

FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY ai/ ./ai/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
