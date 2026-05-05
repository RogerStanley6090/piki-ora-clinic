"""Forms for patient registration and login."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class PatientRegistrationForm(UserCreationForm):
    """Sign-up form for patients.

    Forces `role = patient` regardless of any tampering in the POST data so
    that nobody can self-promote to admin from the public registration page.
    """

    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(
        max_length=32,
        required=False,
        help_text="Optional. Used by the clinic to contact you about appointments.",
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "phone",
            "password1",
            "password2",
        )

    def save(self, commit: bool = True) -> User:
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data.get("phone", "")
        # Public sign-ups are always patients.
        user.role = User.Roles.PATIENT
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Thin wrapper so we can apply Bootstrap classes via widget_tweaks."""

    username = forms.CharField(
        label="Username",
        widget=forms.TextInput(attrs={"autofocus": True, "autocomplete": "username"}),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
