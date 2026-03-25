from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from accounts.decorators import donor_required, hospital_required
from .models import DemandeUrgente, Don, ReponseAppel, BLOOD_COMPATIBILITY
from .forms import DemandeUrgenteForm, DonForm


def home(request):
    return render(request, 'home.html')


# ─── Donor views ────────────────────────────────────────────────────────────

@donor_required
def donor_dashboard(request):
    donneur = getattr(request.user, 'donneur', None)
    if donneur is None:
        messages.error(request, "Profil donneur introuvable.")
        return redirect('home')

    compatible_types = BLOOD_COMPATIBILITY.get(donneur.groupe_sanguin, [])
    demandes = DemandeUrgente.objects.filter(
        statut=DemandeUrgente.Statut.ACTIVE,
        groupe_sanguin__in=compatible_types,
        delai__gte=timezone.now().date(),
    ).select_related('hopital')

    dons = donneur.dons.filter(valide=True).order_by('-date_don')[:5]

    # IDs of demandes already responded to
    reponses_ids = set(
        ReponseAppel.objects.filter(donneur=donneur).values_list('demande_id', flat=True)
    )

    # Upcoming campaign reminder
    from .models import Inscription
    upcoming_inscription = donneur.inscriptions.filter(
        campagne__date__gte=timezone.now().date()
    ).select_related('campagne').first()

    return render(request, 'donor/dashboard.html', {
        'donneur': donneur,
        'demandes': demandes,
        'dons': dons,
        'reponses_ids': reponses_ids,
        'upcoming_inscription': upcoming_inscription,
    })


@donor_required
def respond_demande(request, pk):
    donneur = request.user.donneur
    demande = get_object_or_404(DemandeUrgente, pk=pk, statut=DemandeUrgente.Statut.ACTIVE)

    if not donneur.actif:
        messages.error(request, "Votre compte est marqué comme indisponible. Activez-le dans votre profil.")
        return redirect('donor:dashboard')

    compatible_types = BLOOD_COMPATIBILITY.get(donneur.groupe_sanguin, [])
    if demande.groupe_sanguin not in compatible_types:
        messages.error(request, f"Votre groupe sanguin ({donneur.groupe_sanguin}) n'est pas compatible avec cette demande ({demande.groupe_sanguin}).")
        return redirect('donor:dashboard')

    if not donneur.est_eligible():
        prochaine = donneur.get_prochaine_date_eligibilite()
        messages.error(request, f"Vous n'êtes pas encore éligible au don. Prochaine date : {prochaine.strftime('%d/%m/%Y')}.")
        return redirect('donor:dashboard')

    if ReponseAppel.objects.filter(demande=demande, donneur=donneur).exists():
        messages.warning(request, "Vous avez déjà répondu à cet appel.")
        return redirect('donor:dashboard')

    ReponseAppel.objects.create(demande=demande, donneur=donneur)
    messages.success(request, f"Votre réponse a été enregistrée. L'hôpital {demande.hopital.nom} vous contactera.")
    return redirect('donor:dashboard')


@donor_required
def record_don(request):
    donneur = request.user.donneur
    if not donneur.est_eligible():
        prochaine = donneur.get_prochaine_date_eligibilite()
        messages.error(request, f"Vous ne pouvez pas enregistrer un don avant le {prochaine.strftime('%d/%m/%Y')} ({donneur.get_delai_jours()} jours entre chaque don).")
        return redirect('donor:dashboard')

    if request.method == 'POST':
        form = DonForm(request.POST)
        if form.is_valid():
            don = form.save(commit=False)
            don.donneur = donneur
            don.save()
            messages.success(request, "Don enregistré avec succès.")
            return redirect('donor:dashboard')
    else:
        form = DonForm()
    return render(request, 'donor/record_don.html', {'form': form})


# ─── Hospital views ──────────────────────────────────────────────────────────

@hospital_required
def hospital_dashboard(request):
    hopital = getattr(request.user, 'hopital', None)
    if hopital is None:
        messages.error(request, "Profil hôpital introuvable.")
        return redirect('home')

    demandes_actives = hopital.demandes.filter(statut=DemandeUrgente.Statut.ACTIVE)
    campagnes = hopital.campagnes.all()[:3]

    return render(request, 'hospital/dashboard.html', {
        'hopital': hopital,
        'demandes_actives': demandes_actives,
        'campagnes': campagnes,
    })


@hospital_required
def create_demande(request):
    hopital = request.user.hopital
    if not hopital.valide:
        messages.error(request, "Votre compte doit être validé par l'administrateur avant de publier des demandes.")
        return redirect('hospital:dashboard')

    if request.method == 'POST':
        form = DemandeUrgenteForm(request.POST)
        if form.is_valid():
            demande = form.save(commit=False)
            demande.hopital = hopital
            demande.save()
            messages.success(request, "Demande urgente publiée avec succès.")
            return redirect('hospital:demande_history')
    else:
        form = DemandeUrgenteForm()
    return render(request, 'hospital/create_demande.html', {'form': form})


@hospital_required
def edit_demande(request, pk):
    hopital = request.user.hopital
    demande = get_object_or_404(DemandeUrgente, pk=pk, hopital=hopital)

    if request.method == 'POST':
        form = DemandeUrgenteForm(request.POST, instance=demande)
        if form.is_valid():
            form.save()
            messages.success(request, "Demande mise à jour.")
            return redirect('hospital:demande_history')
    else:
        form = DemandeUrgenteForm(instance=demande)
    return render(request, 'hospital/edit_demande.html', {'form': form, 'demande': demande})


@hospital_required
def close_demande(request, pk):
    hopital = request.user.hopital
    demande = get_object_or_404(DemandeUrgente, pk=pk, hopital=hopital)
    demande.statut = DemandeUrgente.Statut.CLOTUREE
    demande.save()
    messages.success(request, "Demande clôturée.")
    return redirect('hospital:demande_history')


@hospital_required
def demande_history(request):
    hopital = request.user.hopital
    demandes = hopital.demandes.all()

    statut_filter = request.GET.get('statut', '')
    if statut_filter:
        demandes = demandes.filter(statut=statut_filter)

    paginator = Paginator(demandes, 10)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'hospital/demande_history.html', {
        'page_obj': page,
        'statut_filter': statut_filter,
        'statut_choices': DemandeUrgente.Statut.choices,
    })


@hospital_required
def demande_respondents(request, pk):
    hopital = request.user.hopital
    demande = get_object_or_404(DemandeUrgente, pk=pk, hopital=hopital)
    reponses = demande.reponses.select_related('donneur__user').order_by('-date_reponse')

    return render(request, 'hospital/demande_respondents.html', {
        'demande': demande,
        'reponses': reponses,
    })
