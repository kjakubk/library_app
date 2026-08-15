#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Automatyczne utworzenie konta administratora (ze zmiennych środowiskowych)
python create_admin.py
