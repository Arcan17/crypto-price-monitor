from django.apps import AppConfig


class MonitorConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitor"

    def ready(self) -> None:
        from .signals import setup_periodic_tasks  # noqa: F401
