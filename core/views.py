from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from accounts.decorators import donor_required, hospital_required
from django.db import transaction
from .models import DemandeUrgente, Don, ReponseAppel, Campagne, Inscription, BLOOD_COMPATIBILITY
from .forms import DemandeUrgenteForm, DonForm, CampagneForm, InscriptionForm


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

    # Notify donor of cancelled campaigns they were registered for
    cancelled = donneur.inscriptions.filter(campagne__annulee=True).select_related('campagne')
    for insc in cancelled:
        messages.warning(request, f"La campagne « {insc.campagne.nom} » du {insc.campagne.date.strftime('%d/%m/%Y')} a été annulée par l'hôpital.")

    # IDs of demandes already responded to
    reponses_ids = set(
        ReponseAppel.objects.filter(donneur=donneur).values_list('demande_id', flat=True)
    )

    # Upcoming campaign reminder
    upcoming_inscription = donneur.inscriptions.filter(
        campagne__date__gte=timezone.now().date(),
        campagne__annulee=False,
    ).select_related('campagne').order_by('campagne__date').first()

    days_until = None
    if upcoming_inscription:
        days_until = (upcoming_inscription.campagne.date - timezone.now().date()).days

    return render(request, 'donor/dashboard.html', {
        'donneur': donneur,
        'demandes': demandes,
        'dons': dons,
        'reponses_ids': reponses_ids,
        'upcoming_inscription': upcoming_inscription,
        'days_until': days_until,
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
    campagnes = hopital.campagnes.filter(annulee=False)[:3]
    campagnes_actives_count = hopital.campagnes.filter(annulee=False).count()

    return render(request, 'hospital/dashboard.html', {
        'hopital': hopital,
        'demandes_actives': demandes_actives,
        'campagnes': campagnes,
        'campagnes_actives_count': campagnes_actives_count,
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
def delete_demande(request, pk):
    hopital = request.user.hopital
    demande = get_object_or_404(DemandeUrgente, pk=pk, hopital=hopital)
    demande.delete()
    messages.success(request, "Demande supprimée.")
    return redirect('hospital:demande_history')


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


# ─── Campaign views (Hospital) ───────────────────────────────────────────────

@hospital_required
def create_campagne(request):
    hopital = request.user.hopital
    if not hopital.valide:
        messages.error(request, "Votre compte doit être validé pour créer des campagnes.")
        return redirect('hospital:dashboard')

    if request.method == 'POST':
        form = CampagneForm(request.POST)
        if form.is_valid():
            campagne = form.save(commit=False)
            campagne.hopital = hopital
            campagne.save()
            messages.success(request, f"Campagne « {campagne.nom} » créée avec succès.")
            return redirect('hospital:campagne_list')
    else:
        form = CampagneForm()
    return render(request, 'hospital/create_campagne.html', {'form': form})


@hospital_required
def edit_campagne(request, pk):
    hopital = request.user.hopital
    campagne = get_object_or_404(Campagne, pk=pk, hopital=hopital)

    if request.method == 'POST':
        form = CampagneForm(request.POST, instance=campagne)
        if form.is_valid():
            form.save()
            messages.success(request, "Campagne mise à jour.")
            return redirect('hospital:campagne_list')
    else:
        form = CampagneForm(instance=campagne)
    return render(request, 'hospital/edit_campagne.html', {'form': form, 'campagne': campagne})


@hospital_required
def cancel_campagne(request, pk):
    hopital = request.user.hopital
    campagne = get_object_or_404(Campagne, pk=pk, hopital=hopital)
    campagne.annulee = True
    campagne.save()
    messages.warning(request, f"Campagne « {campagne.nom} » annulée. Les donneurs inscrits seront informés à leur prochaine connexion.")
    return redirect('hospital:campagne_list')


@hospital_required
def campagne_list(request):
    hopital = request.user.hopital
    campagnes = hopital.campagnes.order_by('date')
    return render(request, 'hospital/campagne_list.html', {'campagnes': campagnes})


@hospital_required
def campagne_attendees(request, pk):
    hopital = request.user.hopital
    campagne = get_object_or_404(Campagne, pk=pk, hopital=hopital)
    inscriptions = campagne.inscriptions.select_related('donneur__user').order_by('creneau_horaire')

    if request.method == 'POST':
        inscription_id = request.POST.get('inscription_id')
        present_val = request.POST.get('present') == 'true'
        insc = get_object_or_404(Inscription, pk=inscription_id, campagne=campagne)
        insc.present = present_val
        insc.save()
        return redirect('hospital:campagne_attendees', pk=pk)

    # Group by creneau_horaire
    from collections import defaultdict
    grouped = defaultdict(list)
    for insc in inscriptions:
        grouped[insc.creneau_horaire].append(insc)

    return render(request, 'hospital/campagne_attendees.html', {
        'campagne': campagne,
        'grouped': dict(grouped),
    })


# ─── Campaign views (Donor) ──────────────────────────────────────────────────

@donor_required
def donor_campagnes(request):
    donneur = request.user.donneur
    today = timezone.now().date()
    campagnes = Campagne.objects.filter(
        date__gte=today,
        annulee=False,
    ).select_related('hopital').order_by('date')

    inscriptions_ids = set(
        donneur.inscriptions.values_list('campagne_id', flat=True)
    )

    return render(request, 'donor/campagnes.html', {
        'campagnes': campagnes,
        'inscriptions_ids': inscriptions_ids,
        'donneur': donneur,
    })


@donor_required
def register_campagne(request, pk):
    donneur = request.user.donneur
    campagne = get_object_or_404(Campagne, pk=pk, annulee=False)

    if Inscription.objects.filter(campagne=campagne, donneur=donneur).exists():
        messages.warning(request, "Vous êtes déjà inscrit à cette campagne.")
        return redirect('donor:campagnes')

    # Blood type check
    groupes = campagne.get_groupes_list()
    if groupes and donneur.groupe_sanguin not in groupes:
        messages.error(request, f"Cette campagne cible les groupes : {', '.join(groupes)}. Votre groupe ({donneur.groupe_sanguin}) n'est pas concerné.")
        return redirect('donor:campagnes')

    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            creneau = form.cleaned_data['creneau_horaire']
            with transaction.atomic():
                # Lock to handle concurrent requests
                campagne_locked = Campagne.objects.select_for_update().get(pk=pk)

                # Check total capacity
                if campagne_locked.est_complete():
                    messages.error(request, "Cette campagne est complète.")
                    return redirect('donor:campagnes')

                # Check per-slot capacity
                slots_count = Inscription.objects.filter(
                    campagne=campagne_locked,
                    creneau_horaire=creneau,
                ).count()
                if slots_count >= campagne_locked.capacite_par_creneau:
                    messages.error(request, f"Le créneau {creneau.strftime('%H:%M')} est complet. Choisissez un autre créneau.")
                    return render(request, 'donor/register_campagne.html', {'form': form, 'campagne': campagne})

                Inscription.objects.create(
                    campagne=campagne_locked,
                    donneur=donneur,
                    creneau_horaire=creneau,
                )
            messages.success(request, f"Inscription confirmée pour « {campagne.nom} » le {campagne.date.strftime('%d/%m/%Y')} à {creneau.strftime('%H:%M')}.")
            return redirect('donor:dashboard')
    else:
        form = InscriptionForm()

    return render(request, 'donor/register_campagne.html', {'form': form, 'campagne': campagne})
