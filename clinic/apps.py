from django.apps import AppConfig


class ClinicConfig(AppConfig):
    """Patient-facing app: doctors, slots, appointments."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "clinic"
    verbose_name = "Clinic"
