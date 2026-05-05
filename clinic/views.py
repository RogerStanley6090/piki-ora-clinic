"""Patient-facing views: browse doctors, view slots, book/edit/cancel appointments."""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import BookingForm, EditAppointmentForm
from .models import Appointment, AppointmentSlot, Doctor


def doctor_list(request: HttpRequest) -> HttpResponse:
    """Public list of doctors at the clinic."""
    doctors = Doctor.objects.all()
    return render(request, "clinic/doctor_list.html", {"doctors": doctors})


def doctor_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Doctor profile with their upcoming available slots."""
    doctor = get_object_or_404(Doctor, pk=pk)
    slots = doctor.upcoming_available_slots
    return render(
        request,
        "clinic/doctor_detail.html",
        {"doctor": doctor, "slots": slots},
    )


@login_required
def book_appointment(request: HttpRequest, slot_id: int) -> HttpResponse:
    """Book the requested slot for the current user."""
    slot = get_object_or_404(AppointmentSlot, pk=slot_id)

    # Quick sanity checks before showing the form.
    if slot.start_time < timezone.now():
        messages.error(request, "That slot is in the past.")
        return redirect("clinic:doctor_detail", pk=slot.doctor_id)
    if not slot.is_available:
        messages.error(request, "That slot is no longer available.")
        return redirect("clinic:doctor_detail", pk=slot.doctor_id)

    if request.method == "POST":
        form = BookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Re-fetch the slot inside the transaction with row locking
                    # so two simultaneous bookings cannot both succeed.
                    locked_slot = AppointmentSlot.objects.select_for_update().get(pk=slot.pk)
                    if not locked_slot.is_available:
                        raise ValidationError("Slot was taken in the last moment.")

                    appointment = form.save(commit=False)
                    appointment.patient = request.user
                    appointment.status = Appointment.Status.CONFIRMED
                    appointment.slot = locked_slot
                    appointment.full_clean()
                    appointment.save()

                    locked_slot.is_available = False
                    locked_slot.save(update_fields=["is_available"])
            except (IntegrityError, ValidationError) as exc:
                messages.error(request, f"Could not complete booking: {exc}")
                return redirect("clinic:doctor_detail", pk=slot.doctor_id)

            # Send a confirmation email — never block the booking on failure.
            recipient_email = getattr(request.user, "email", "") or ""
            if recipient_email:
                try:
                    send_mail(
                        subject="Appointment Confirmed - Piki Ora Medical Centre",
                        message=(
                            f"Kia ora {request.user.first_name or request.user.username},\n\n"
                            f"Your appointment with {slot.doctor} is confirmed for "
                            f"{slot.start_time:%a %d %b %Y at %H:%M}.\n\n"
                            "You can view, edit or cancel this booking at any time from the "
                            "'My Appointments' page after signing in.\n\n"
                            "Nga mihi,\n"
                            "Piki Ora Medical Centre"
                        ),
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient_email],
                        fail_silently=True,
                    )
                except Exception:  # noqa: BLE001 — email must never block booking
                    pass

            messages.success(
                request,
                f"Appointment confirmed with {slot.doctor} at {slot.start_time:%a %d %b %Y %H:%M}.",
            )
            return redirect("clinic:my_appointments")
    else:
        form = BookingForm(initial={"slot": slot})

    return render(
        request,
        "clinic/book_appointment.html",
        {"form": form, "slot": slot},
    )


@login_required
def my_appointments(request: HttpRequest) -> HttpResponse:
    """List the current user's appointments, upcoming first."""
    qs = (
        Appointment.objects.filter(patient=request.user)
        .select_related("slot", "slot__doctor")
        .order_by("-slot__start_time")
    )
    now = timezone.now()
    upcoming = [a for a in qs if a.slot.start_time >= now and a.status == Appointment.Status.CONFIRMED]
    past = [a for a in qs if a.slot.start_time < now or a.status == Appointment.Status.CANCELLED]
    return render(
        request,
        "clinic/my_appointments.html",
        {"upcoming": upcoming, "past": past},
    )


@login_required
def edit_appointment(request: HttpRequest, pk: int) -> HttpResponse:
    """Let a patient update the reason for an upcoming appointment."""
    appointment = get_object_or_404(
        Appointment.objects.select_related("slot", "slot__doctor"),
        pk=pk,
        patient=request.user,
    )
    if appointment.status == Appointment.Status.CANCELLED:
        messages.error(request, "Cancelled appointments cannot be edited.")
        return redirect("clinic:my_appointments")
    if appointment.slot.is_past:
        messages.error(request, "Past appointments cannot be edited.")
        return redirect("clinic:my_appointments")

    if request.method == "POST":
        form = EditAppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment updated.")
            return redirect("clinic:my_appointments")
    else:
        form = EditAppointmentForm(instance=appointment)

    return render(
        request,
        "clinic/edit_appointment.html",
        {"form": form, "appointment": appointment},
    )


@login_required
def cancel_appointment(request: HttpRequest, pk: int) -> HttpResponse:
    """Confirm and then cancel a patient's appointment, freeing the slot."""
    appointment = get_object_or_404(
        Appointment.objects.select_related("slot", "slot__doctor"),
        pk=pk,
        patient=request.user,
    )

    if request.method == "POST":
        if appointment.status == Appointment.Status.CANCELLED:
            messages.info(request, "That appointment was already cancelled.")
            return redirect("clinic:my_appointments")
        with transaction.atomic():
            appointment.status = Appointment.Status.CANCELLED
            appointment.save(update_fields=["status", "updated_at"])
            # Free the slot so another patient can book it (if it's still in the future).
            slot = appointment.slot
            if not slot.is_past:
                slot.is_available = True
                slot.save(update_fields=["is_available"])
        messages.success(request, "Your appointment has been cancelled.")
        return redirect("clinic:my_appointments")

    return render(
        request,
        "clinic/cancel_appointment.html",
        {"appointment": appointment},
    )
