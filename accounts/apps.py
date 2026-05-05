from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts app (custom user, registration, login)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Accounts"
