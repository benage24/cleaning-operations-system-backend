#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
<<<<<<< HEAD
python manage.py seed_demo_data --if-empty
=======
>>>>>>> develop

exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
