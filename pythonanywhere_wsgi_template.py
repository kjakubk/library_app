# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Plik konfiguracyjny WSGI dla PythonAnywhere (skopiuj do /var/www/twojuser_pythonanywhere_com_wsgi.py)
# ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

import os
import sys

# 1. Ścieżka do Twojego projektu (zmień 'twojuser' na swój dokładny login z PythonAnywhere)
path = '/home/twojuser/library_app'
if path not in sys.path:
    sys.path.insert(0, path)

# Ustawiamy katalog roboczy na folder projektu
os.chdir(path)

# 2. Ustawienie modułu ustawień Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'

# 3. Załadowanie aplikacji Django WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
