"""
Custom user model for the Piki Ora Medical Centre Appointment System.

Why a custom user?
- We need a `role` field to distinguish patients from clinic admins.
- Using AbstractUser keeps Django's built-in username/password/email/etc., so
  authentication, password hashing and the admin-style helpers (is_authenticated
  etc.) all keep working out of the box.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Application user — either a patient or a clinic admin."""

    class Roles(models.TextChoices):
        PATIENT = "patient", "Patient"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=10,
        choices=Roles.choices,
        default=Roles.PATIENT,
        help_text="Determines whether the user sees the patient UI or the admin dashboard.",
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        help_text="Optional contact phone number.",
    )

    # ---- Convenience helpers --------------------------------------------------
    @property
    def is_patient(self) -> bool:
        return self.role == self.Roles.PATIENT

    @property
    def is_clinic_admin(self) -> bool:
        # Note: avoid the name `is_admin` to prevent confusion with Django's
        # `is_staff` / `is_superuser` flags.
        return self.role == self.Roles.ADMIN

    def __str__(self) -> str:
        full = self.get_full_name() or self.username
        return f"{full} ({self.get_role_display()})"
