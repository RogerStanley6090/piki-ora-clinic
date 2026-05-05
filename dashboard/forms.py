"""ModelForms used by the custom admin dashboard."""

from django import forms
from django.contrib.auth import get_user_model

from clinic.models import Appointment, AppointmentSlot, Doctor

User = get_user_model()


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = ("name", "specialization", "email", "phone", "bio", "photo_url")
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
        }


class SlotForm(forms.ModelForm):
    class Meta:
        model = AppointmentSlot
        fields = ("doctor", "start_time", "end_time", "is_available")
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
            "end_time": forms.DateTimeInput(
                attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The browser sends datetimes in this exact format.
        self.fields["start_time"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_time"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        doctor = cleaned.get("doctor")
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        # Reject any slot that overlaps another slot for the same doctor.
        # Two windows [s1, e1) and [s2, e2) overlap when s1 < e2 AND s2 < e1.
        if doctor and start and end:
            overlapping = AppointmentSlot.objects.filter(
                doctor=doctor,
                start_time__lt=end,
                end_time__gt=start,
            )
            if self.instance and self.instance.pk:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            if overlapping.exists():
                raise forms.ValidationError(
                    "This slot overlaps with another existing slot for the same doctor."
                )
        return cleaned


class AppointmentForm(forms.ModelForm):
    """Admin-side editing of an appointment (status + reason)."""

    class Meta:
        model = Appointment
        fields = ("status", "reason")
        widgets = {
            "reason": forms.Textarea(attrs={"rows": 3}),
        }


class UserEditForm(forms.ModelForm):
    """Admin-side editing of a user account."""

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "is_active",
        )
