from django.shortcuts import redirect
from django.conf import settings
from django.urls import reverse


class RequireLoginMiddleware:
    """
    Middleware wymuszający zalogowanie dla wszystkich podstron w serwisie.
    Wyjątki stanowią: strona logowania, panel administracyjny oraz pliki statyczne/media.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            # Lista ścieżek dostępnych bez logowania
            allowed_prefixes = [
                '/logowanie/',
                '/admin/',
                '/static/',
                '/media/',
            ]
            
            try:
                login_url = reverse(settings.LOGIN_URL)
                if login_url not in allowed_prefixes:
                    allowed_prefixes.append(login_url)
            except Exception:
                pass

            path = request.path_info

            # Jeśli ścieżka nie znajduje się na liście dozwolonych, przekieruj do logowania
            if not any(path.startswith(prefix) for prefix in allowed_prefixes):
                return redirect(f"{reverse('login')}?next={request.path}")

        return self.get_response(request)
