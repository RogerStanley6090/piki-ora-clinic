"""Forms used by patients to book and edit appointments."""

from django import forms
from django.utils import timezone

from .models import Appointment, AppointmentSlot


class BookingForm(forms.ModelForm):
    """Patient-facing booking form.

    The slot is supplied by the URL (so the field is hidden); the patient only
    fills in the reason for the visit. We re-validate slot availability inside
    ``clean_slot`` to guard against the (unlikely) race where two patients try
    to book the same slot simultaneously.
    """

    class Meta:
        model = Appointment
        fields = ("slot", "reason")
        widgets = {
            "slot": forms.HiddenInput(),
            "reason": forms.Textarea(attrs={"rows": 4, "placeholder": "Briefly describe your symptoms or reason for visit."}),
        }

    def clean_slot(self) -> AppointmentSlot:
        slot: AppointmentSlot = self.cleaned_data["slot"]
        if slot.start_time < timezone.now():
            raise forms.ValidationError("That slot is in the past — please pick a future time.")
        if not slot.is_available:
            raise forms.ValidationError("Sorry, that slot has just been taken. Please pick another.")
        # Belt-and-braces: also check there is no existing confirmed appointment.
        if Appointment.objects.filter(
            slot=slot, status=Appointment.Status.CONFIRMED
        ).exists():
            raise forms.ValidationError("That slot is already booked.")
        return slot


class EditAppointmentForm(forms.ModelForm):
    """Allow a patient to update the reason for an upcoming appointment.

    We deliberately do NOT let patients change the slot via this form — to
    move to a new time they should cancel the existing booking and book again.
    """

    class Meta:
        model = Appointment
        fields = ("reason",)
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 4}),
        }
