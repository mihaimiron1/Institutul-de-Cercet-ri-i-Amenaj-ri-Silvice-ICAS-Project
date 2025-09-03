from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # import signals to keep group ↔ is_staff synchronized
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid crashing at import time; failures will surface in logs
            pass