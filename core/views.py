from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import donor_required, hospital_required


def home(request):
    return render(request, 'home.html')


@donor_required
def donor_dashboard(request):
    donneur = getattr(request.user, 'donneur', None)
    if donneur is None:
        from django.contrib import messages
        messages.error(request, "Profil donneur introuvable.")
        return redirect('home')
    return render(request, 'donor/dashboard.html', {'donneur': donneur})


@hospital_required
def hospital_dashboard(request):
    hopital = getattr(request.user, 'hopital', None)
    if hopital is None:
        from django.contrib import messages
        messages.error(request, "Profil hôpital introuvable.")
        return redirect('home')
    return render(request, 'hospital/dashboard.html', {'hopital': hopital})
