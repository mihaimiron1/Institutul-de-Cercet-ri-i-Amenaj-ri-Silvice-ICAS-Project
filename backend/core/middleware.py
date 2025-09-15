import re
from django.conf import settings
from django.shortcuts import redirect
from django.urls import resolve


class LoginRequiredMiddleware:
    """Require authentication for all views, except a small whitelist.

    Exempts:
      - settings.LOGIN_URL and all /accounts/* endpoints
      - /admin/login/
      - static and media files (for login page assets)
      - any regex in settings.LOGIN_EXEMPT_URLS (optional)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Precompile exemption patterns
        default_exempt = [
            r"^%s$" % settings.LOGIN_URL.lstrip('/'),
            r"^accounts/",
            r"^admin/login/",
            r"^static/",
            r"^media/",
        ]
        extra = getattr(settings, 'LOGIN_EXEMPT_URLS', []) or []
        self.exempt_patterns = [re.compile(p) for p in [*default_exempt, *extra]]

    def __call__(self, request):
        user = getattr(request, 'user', None)

        path = request.path.lstrip('/')

        is_exempt = any(p.match(path) for p in self.exempt_patterns)

        if not is_exempt and (user is None or not user.is_authenticated):
            # Avoid loop: if already going to LOGIN_URL, allow
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")

        return self.get_response(request)


