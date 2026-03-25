from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def donor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_donneur() or request.user.is_admin_user():
            messages.warning(request, "Accès réservé aux donneurs.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def hospital_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_hopital():
            messages.warning(request, "Accès réservé aux établissements hospitaliers.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_admin_user():
            messages.warning(request, "Accès réservé aux administrateurs.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
