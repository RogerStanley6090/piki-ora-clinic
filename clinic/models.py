"""
Models for doctors, appointment slots and patient appointments.

Double-booking is prevented in three layers:
1. ``AppointmentSlot`` has a ``unique_together`` constraint on (doctor, start_time)
   so the same doctor cannot be given two slots starting at the same instant.
2. ``Appointment.slot`` is a ``OneToOneField`` — at the database level a slot can
   only be linked to one appointment ever.
3. ``Appointment.clean()`` and ``BookingForm.clean()`` validate that the slot is
   still available and not already booked. The booking view wraps the writes in
   a ``transaction.atomic`` block so the slot flag and the appointment row are
   updated together.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Doctor(models.Model):
    """A medical professional that patients can book with."""

    name = models.CharField(max_length=150)
    specialization = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    bio = models.TextField(blank=True, help_text="Short biography shown on the doctor's page.")
    photo_url = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional URL to a profile photo. Plain text to keep deployments simple.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        return f"Dr. {self.name} ({self.specialization})"

    @property
    def upcoming_available_slots(self):
        """Convenience: future slots that are still bookable."""
        return self.slots.filter(
            is_available=True,
            start_time__gte=timezone.now(),
        ).order_by("start_time")


class AppointmentSlot(models.Model):
    """A single bookable time window for a particular doctor."""

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="slots",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField(
        default=True,
        help_text="Set to False once the slot is booked or otherwise blocked.",
    )

    class Meta:
        ordering = ("start_time",)
        constraints = [
            models.UniqueConstraint(
                fields=("doctor", "start_time"),
                name="unique_doctor_start_time",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.doctor.name} @ {self.start_time:%a %d %b %Y %H:%M}"

    def clean(self) -> None:
        """Validate the slot itself before saving."""
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError("End time must be after start time.")

    @property
    def is_past(self) -> bool:
        return self.start_time < timezone.now()


class Appointment(models.Model):
    """A patient's booking against a single AppointmentSlot."""

    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    # OneToOne enforces "at most one appointment per slot" at the DB level —
    # this is the strongest guarantee against double-booking.
    slot = models.OneToOneField(
        AppointmentSlot,
        on_delete=models.PROTECT,
        related_name="appointment",
    )
    reason = models.TextField(
        blank=True,
        help_text="Patient-supplied reason for the visit.",
    )
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.CONFIRMED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.patient} -> {self.slot}"

    def clean(self) -> None:
        """Defensive validation, layered on top of the DB constraints."""
        if self.slot_id and self.status == self.Status.CONFIRMED:
            # A slot may only host a single CONFIRMED appointment; reuse is
            # only permitted via the same row (i.e. editing an existing row).
            qs = Appointment.objects.filter(slot=self.slot, status=self.Status.CONFIRMED)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("This slot is already booked. Please pick another time.")
