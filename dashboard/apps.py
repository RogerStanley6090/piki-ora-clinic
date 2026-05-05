from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """Custom admin dashboard app — replaces Django's built-in admin."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    verbose_name = "Dashboard"
