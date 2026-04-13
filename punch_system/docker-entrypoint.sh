#!/bin/sh
set -eu

if [ "${RUN_DB_SETUP:-1}" = "1" ]; then
  python setup_database.py
fi

exec gunicorn \
  --bind "0.0.0.0:${PORT:-5001}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --threads "${GUNICORN_THREADS:-8}" \
  --worker-class gthread \
  --timeout "${GUNICORN_TIMEOUT:-60}" \
  --access-logfile - \
  --error-logfile - \
  app:app
