"""
Top-level URL configuration for the Piki Ora Medical Centre Appointment System.

The Django built-in admin (django.contrib.admin) is intentionally NOT mounted
here. Per the assignment requirements, all administrative actions live in the
custom dashboard app at /dashboard/.
"""

from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    # Public landing page.
    path("", TemplateView.as_view(template_name="home.html"), name="home"),

    # Patient-facing authentication & profile.
    path("accounts/", include("accounts.urls")),

    # Patient-facing clinic functionality (doctors, slots, bookings).
    path("clinic/", include("clinic.urls")),

    # Custom admin dashboard (replaces Django admin).
    path("dashboard/", include("dashboard.urls")),
]
