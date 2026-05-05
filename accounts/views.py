"""Views for registration, login, logout and profile."""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .forms import LoginForm, PatientRegistrationForm


def register_view(request: HttpRequest) -> HttpResponse:
    """Register a new patient account, then auto-login and redirect home."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f"Welcome to Piki Ora, {user.first_name}! Your account is ready.",
            )
            return redirect("home")
    else:
        form = PatientRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


class CustomLoginView(LoginView):
    """Class-based login view backed by our Bootstrap-styled LoginForm."""

    authentication_form = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        # Send admins straight to the dashboard so they don't have to navigate.
        user = self.request.user
        if user.is_authenticated and getattr(user, "is_clinic_admin", False):
            return reverse_lazy("dashboard:home")
        return reverse_lazy("home")


def logout_view(request: HttpRequest) -> HttpResponse:
    """Log the user out and return to the public landing page."""
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been logged out.")
    return redirect("home")


@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Show the currently logged-in user's profile information."""
    return render(request, "accounts/profile.html", {"profile_user": request.user})
