"""URL routes for the custom admin dashboard."""

from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),

    # Doctors
    path("doctors/", views.doctors_list, name="doctors_list"),
    path("doctors/new/", views.doctor_create, name="doctor_create"),
    path("doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),

    # Slots
    path("slots/", views.slots_list, name="slots_list"),
    path("slots/new/", views.slot_create, name="slot_create"),
    path("slots/<int:pk>/edit/", views.slot_edit, name="slot_edit"),
    path("slots/<int:pk>/delete/", views.slot_delete, name="slot_delete"),

    # Appointments
    path("appointments/", views.appointments_list, name="appointments_list"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("appointments/<int:pk>/cancel/", views.appointment_cancel, name="appointment_cancel"),

    # Users
    path("users/", views.users_list, name="users_list"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
]
