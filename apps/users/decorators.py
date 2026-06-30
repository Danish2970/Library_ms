# ── decorators.py ─────────────────────────────────────────────────────────────
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def librarian_required(view_func):
    """Only librarians can access this view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not request.user.is_librarian():
            messages.error(request, "Access denied. Librarian account required.")
            return redirect('analytics:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Only students can access this view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not request.user.is_student():
            messages.error(request, "This page is for students only.")
            return redirect('analytics:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper