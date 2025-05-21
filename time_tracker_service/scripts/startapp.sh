#!/bin/bash

echo 'RUNNING MIGRATIONS:'
alembic upgrade head
echo 'MIGRATIONS RAN. EXITING'

uvicorn app.main:app --port 8002 --host 0.0.0.0 --workers 4