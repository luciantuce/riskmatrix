#!/bin/sh
set -e

# Run migrations on every boot. Alembic is idempotent — safe to re-run.
echo "==> Running Alembic migrations"
alembic upgrade head

# Railway injects $PORT. Fall back to 8010 for local / non-Railway runs.
PORT="${PORT:-8010}"
echo "==> Starting uvicorn on 0.0.0.0:${PORT}"
if [ "${UVICORN_RELOAD:-}" = "1" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port "${PORT}" --reload
else
  exec uvicorn main:app --host 0.0.0.0 --port "${PORT}"
fi
