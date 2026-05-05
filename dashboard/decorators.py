"""Decorators that protect dashboard views."""

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden


def admin_required(view_func):
    """Allow access only to authenticated users whose role == 'admin'.

    - Anonymous users are bounced through @login_required to /accounts/login/.
    - Authenticated non-admins get a clean 403 page.
    """

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        user = request.user
        if not getattr(user, "is_clinic_admin", False):
            return HttpResponseForbidden(
                "<h1>403 Forbidden</h1>"
                "<p>You need an admin account to access the dashboard.</p>"
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
