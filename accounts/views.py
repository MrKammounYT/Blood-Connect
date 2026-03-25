from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import DonneurRegistrationForm, HopitalRegistrationForm, DonneurProfileForm, HopitalProfileForm


def register_donneur(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = DonneurRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Inscription réussie ! Bienvenue sur BloodConnect.")
            return redirect('donor:dashboard')
    else:
        form = DonneurRegistrationForm()
    return render(request, 'accounts/register_donneur.html', {'form': form})


def register_hopital(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = HopitalRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Demande d'inscription envoyée. Votre compte sera activé après validation par l'administrateur.")
            return redirect('accounts:login')
    else:
        form = HopitalRegistrationForm()
    return render(request, 'accounts/register_hopital.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return _redirect_by_role(request.user)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return _redirect_by_role(user)
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect('accounts:login')


def _redirect_by_role(user):
    if user.is_hopital():
        return redirect('hospital:dashboard')
    if user.is_donneur():
        return redirect('donor:dashboard')
    return redirect('home')


@login_required
def profile_donneur(request):
    if not request.user.is_donneur() or request.user.is_admin_user():
        return redirect('home')
    donneur = request.user.donneur
    if request.method == 'POST':
        form = DonneurProfileForm(request.POST, instance=donneur, user=request.user)
        if form.is_valid():
            form.save_user(request.user)
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('accounts:profile_donneur')
    else:
        form = DonneurProfileForm(instance=donneur, user=request.user)
    return render(request, 'accounts/profile_donneur.html', {'form': form, 'donneur': donneur})


@login_required
def profile_hopital(request):
    if not request.user.is_hopital():
        return redirect('home')
    hopital = request.user.hopital
    if request.method == 'POST':
        form = HopitalProfileForm(request.POST, instance=hopital, user=request.user)
        if form.is_valid():
            form.save_user(request.user)
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect('accounts:profile_hopital')
    else:
        form = HopitalProfileForm(instance=hopital, user=request.user)
    return render(request, 'accounts/profile_hopital.html', {'form': form, 'hopital': hopital})
