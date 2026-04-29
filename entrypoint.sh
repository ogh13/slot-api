#!/bin/bash
set -e
echo "==> DATABASE_URL=$DATABASE_URL"
echo "Apply migrations"
alembic upgrade head
echo "Start API"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000