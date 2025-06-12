#!/bin/sh

set -e

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Running fill_data..."
python manage.py fill_data

echo "==> Starting server..."
exec "$@"
