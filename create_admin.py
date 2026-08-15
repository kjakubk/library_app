import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.contrib.auth.models import User

username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'jakub')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'jakub@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin1234')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"[OK] Pomyślnie utworzono konto administratora: '{username}'")
else:
    # Upewniamy się, że hasło jest zgodne
    user = User.objects.get(username=username)
    if os.environ.get('DJANGO_SUPERUSER_PASSWORD'):
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        print(f"[OK] Zaktualizowano hasło administratora: '{username}'")
