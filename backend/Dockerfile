FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN chmod +x /app/start.sh || true

EXPOSE 8010
# Default CMD for plain `docker run`. docker-compose overrides with start.sh
# (migrations + uvicorn); set UVICORN_RELOAD=1 in env for --reload.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8010", "--reload"]
