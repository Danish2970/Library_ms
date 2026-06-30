from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser
from .forms import StudentRegistrationForm, ProfileUpdateForm
from .decorators import librarian_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('analytics:dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next', 'analytics:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('users:login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('analytics:dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'STUDENT'
            user.save()
            login(request, user)
            messages.success(request, "Account created! Welcome to the library.")
            return redirect('analytics:dashboard')
    else:
        form = StudentRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('users:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'borrow_count': request.user.get_borrow_count(),
        'active_borrows': request.user.get_active_borrows(),
    }
    return render(request, 'users/profile.html', context)