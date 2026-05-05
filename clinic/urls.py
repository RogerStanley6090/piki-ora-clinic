"""URL routes for the patient-facing clinic app."""

from django.urls import path

from . import views

app_name = "clinic"

urlpatterns = [
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/<int:pk>/", views.doctor_detail, name="doctor_detail"),
    path("book/<int:slot_id>/", views.book_appointment, name="book_appointment"),
    path("my/", views.my_appointments, name="my_appointments"),
    path("appointments/<int:pk>/edit/", views.edit_appointment, name="edit_appointment"),
    path("appointments/<int:pk>/cancel/", views.cancel_appointment, name="cancel_appointment"),
]
