from django.conf import settings

from .debug_utils import DEBUG_ENV, debug_forzato_db


class DebugSuperuserMiddleware:
    """Applica DEBUG da database (toggle superutente) per ogni richiesta."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        settings.DEBUG = DEBUG_ENV or debug_forzato_db()
        return self.get_response(request)
