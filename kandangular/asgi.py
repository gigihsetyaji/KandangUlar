import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kandangular.settings")
from django.core.asgi import get_asgi_application
django_app = get_asgi_application()
from django.conf import settings
from asgiref.wsgi import WsgiToAsgi
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from kandangular.api import api
from kandangular.plugins import create_app

async def health(request):
    return JSONResponse({"status": "ok"})

router = Starlette(routes=[Route("/healthz", health), Mount("/api", app=api), Mount("/plugins", app=WsgiToAsgi(create_app())), Mount("/", app=django_app)])
if not settings.DEBUG:
    router = HTTPSRedirectMiddleware(router)
router = TrustedHostMiddleware(router, allowed_hosts=settings.ALLOWED_HOSTS, www_redirect=False)

class SecurityHeaders:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        async def secured_send(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                defaults = {b"x-content-type-options": b"nosniff", b"x-frame-options": b"DENY", b"referrer-policy": b"same-origin", b"permissions-policy": b"camera=(), microphone=(), geolocation=()"}
                # Django admin uses inline scripts; each surface has its own CSP.
                if not scope.get("path", "").startswith(("/admin/", "/api/docs")):
                    defaults[b"content-security-policy"] = b"default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
                if not settings.DEBUG:
                    defaults[b"strict-transport-security"] = b"max-age=31536000; includeSubDomains; preload"
                existing = {key.lower() for key, _ in headers}
                headers.extend((key, value) for key, value in defaults.items() if key not in existing)
                message = {**message, "headers": headers}
            await send(message)
        await self.app(scope, receive, secured_send)

application = SecurityHeaders(router)
