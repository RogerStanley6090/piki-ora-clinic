"""Custom admin dashboard views.

Every view here is protected by @admin_required, which short-circuits any
non-admin (anonymous users get bounced to login, signed-in patients get a 403).
"""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from clinic.models import Appointment, AppointmentSlot, Doctor

from .decorators import admin_required
from .forms import AppointmentForm, DoctorForm, SlotForm, UserEditForm

User = get_user_model()


# ===========================================================================
# Dashboard home
# ===========================================================================
@admin_required
def dashboard_home(request: HttpRequest) -> HttpResponse:
    """High-level metrics for the clinic admin."""
    now = timezone.now()
    context = {
        "doctor_count": Doctor.objects.count(),
        "slot_count": AppointmentSlot.objects.count(),
        "available_slot_count": AppointmentSlot.objects.filter(
            is_available=True, start_time__gte=now
        ).count(),
        "appointment_count": Appointment.objects.count(),
        "upcoming_appointments": (
            Appointment.objects.filter(
                status=Appointment.Status.CONFIRMED, slot__start_time__gte=now
            )
            .select_related("patient", "slot", "slot__doctor")
            .order_by("slot__start_time")[:5]
        ),
        "patient_count": User.objects.filter(role=User.Roles.PATIENT).count(),
        "admin_count": User.objects.filter(role=User.Roles.ADMIN).count(),
    }
    return render(request, "dashboard/home.html", context)


# ===========================================================================
# Doctors CRUD
# ===========================================================================
@admin_required
def doctors_list(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "dashboard/doctors_list.html",
        {"doctors": Doctor.objects.all()},
    )


@admin_required
def doctor_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, f"Doctor '{doctor.name}' created.")
            return redirect("dashboard:doctors_list")
    else:
        form = DoctorForm()
    return render(
        request,
        "dashboard/doctor_form.html",
        {"form": form, "verb": "Create"},
    )


@admin_required
def doctor_edit(request: HttpRequest, pk: int) -> HttpResponse:
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Doctor '{doctor.name}' updated.")
            return redirect("dashboard:doctors_list")
    else:
        form = DoctorForm(instance=doctor)
    return render(
        request,
        "dashboard/doctor_form.html",
        {"form": form, "verb": "Edit", "doctor": doctor},
    )


@admin_required
def doctor_delete(request: HttpRequest, pk: int) -> HttpResponse:
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        name = doctor.name
        doctor.delete()
        messages.success(request, f"Doctor '{name}' deleted.")
        return redirect("dashboard:doctors_list")
    return render(
        request,
        "dashboard/doctor_confirm_delete.html",
        {"doctor": doctor},
    )


# ===========================================================================
# Slots CRUD
# ===========================================================================
@admin_required
def slots_list(request: HttpRequest) -> HttpResponse:
    slots = AppointmentSlot.objects.select_related("doctor").order_by("-start_time")
    return render(request, "dashboard/slots_list.html", {"slots": slots})


@admin_required
def slot_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SlotForm(request.POST)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f"Slot for {slot.doctor.name} created.")
            return redirect("dashboard:slots_list")
    else:
        form = SlotForm()
    return render(
        request,
        "dashboard/slot_form.html",
        {"form": form, "verb": "Create"},
    )


@admin_required
def slot_edit(request: HttpRequest, pk: int) -> HttpResponse:
    slot = get_object_or_404(AppointmentSlot, pk=pk)
    if request.method == "POST":
        form = SlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, "Slot updated.")
            return redirect("dashboard:slots_list")
    else:
        form = SlotForm(instance=slot)
    return render(
        request,
        "dashboard/slot_form.html",
        {"form": form, "verb": "Edit", "slot": slot},
    )


@admin_required
def slot_delete(request: HttpRequest, pk: int) -> HttpResponse:
    slot = get_object_or_404(AppointmentSlot, pk=pk)
    if request.method == "POST":
        # Refuse to delete a slot that has a confirmed appointment — the admin
        # must cancel the appointment first to avoid silent data loss.
        if hasattr(slot, "appointment") and slot.appointment.status == Appointment.Status.CONFIRMED:
            messages.error(
                request,
                "Cannot delete a slot with a confirmed appointment. Cancel the appointment first.",
            )
            return redirect("dashboard:slots_list")
        slot.delete()
        messages.success(request, "Slot deleted.")
        return redirect("dashboard:slots_list")
    return render(
        request,
        "dashboard/slot_confirm_delete.html",
        {"slot": slot},
    )


# ===========================================================================
# Appointments CRUD (view, edit, cancel — no manual create; patients book)
# ===========================================================================
@admin_required
def appointments_list(request: HttpRequest) -> HttpResponse:
    appointments = (
        Appointment.objects.select_related("patient", "slot", "slot__doctor")
        .order_by("-slot__start_time")
    )
    return render(
        request,
        "dashboard/appointments_list.html",
        {"appointments": appointments},
    )


@admin_required
def appointment_edit(request: HttpRequest, pk: int) -> HttpResponse:
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "slot", "slot__doctor"), pk=pk
    )
    previous_status = appointment.status
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            with transaction.atomic():
                appointment = form.save()
                # Keep the slot's availability in sync with the appointment status.
                slot = appointment.slot
                if (
                    appointment.status == Appointment.Status.CANCELLED
                    and previous_status != Appointment.Status.CANCELLED
                    and not slot.is_past
                ):
                    slot.is_available = True
                    slot.save(update_fields=["is_available"])
                elif appointment.status == Appointment.Status.CONFIRMED:
                    slot.is_available = False
                    slot.save(update_fields=["is_available"])
            messages.success(request, "Appointment updated.")
            return redirect("dashboard:appointments_list")
    else:
        form = AppointmentForm(instance=appointment)
    return render(
        request,
        "dashboard/appointment_form.html",
        {"form": form, "appointment": appointment},
    )


@admin_required
def appointment_cancel(request: HttpRequest, pk: int) -> HttpResponse:
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "slot", "slot__doctor"), pk=pk
    )
    if request.method == "POST":
        with transaction.atomic():
            if appointment.status != Appointment.Status.CANCELLED:
                appointment.status = Appointment.Status.CANCELLED
                appointment.save(update_fields=["status", "updated_at"])
                slot = appointment.slot
                if not slot.is_past:
                    slot.is_available = True
                    slot.save(update_fields=["is_available"])
        messages.success(request, "Appointment cancelled.")
        return redirect("dashboard:appointments_list")
    return render(
        request,
        "dashboard/appointment_confirm_cancel.html",
        {"appointment": appointment},
    )


# ===========================================================================
# Users CRUD (edit + delete; new patients self-register)
# ===========================================================================
@admin_required
def users_list(request: HttpRequest) -> HttpResponse:
    users = User.objects.all().order_by("username")
    return render(request, "dashboard/users_list.html", {"users": users})


@admin_required
def user_edit(request: HttpRequest, pk: int) -> HttpResponse:
    target_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{target_user.username}' updated.")
            return redirect("dashboard:users_list")
    else:
        form = UserEditForm(instance=target_user)
    return render(
        request,
        "dashboard/user_form.html",
        {"form": form, "target_user": target_user},
    )


@admin_required
def user_delete(request: HttpRequest, pk: int) -> HttpResponse:
    target_user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        # Stop an admin from accidentally deleting themselves.
        if target_user.pk == request.user.pk:
            messages.error(request, "You cannot delete your own account while logged in.")
            return redirect("dashboard:users_list")
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '{username}' deleted.")
        return redirect("dashboard:users_list")
    return render(
        request,
        "dashboard/user_confirm_delete.html",
        {"target_user": target_user},
    )
