from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


BLOOD_GROUPS = [
    ('A+', 'A+'), ('A-', 'A-'),
    ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'),
    ('O+', 'O+'), ('O-', 'O-'),
]

# Compatibility
BLOOD_COMPATIBILITY = {
    'A+':  ['A+', 'A-', 'O+', 'O-'],
    'A-':  ['A-', 'O-'],
    'B+':  ['B+', 'B-', 'O+', 'O-'],
    'B-':  ['B-', 'O-'],
    'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    'AB-': ['A-', 'B-', 'AB-', 'O-'],
    'O+':  ['O+', 'O-'],
    'O-':  ['O-'],
}


class Donneur(models.Model):
    class Sexe(models.TextChoices):
        HOMME = 'M', 'Homme'
        FEMME = 'F', 'Femme'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donneur')
    groupe_sanguin = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    sexe = models.CharField(max_length=1, choices=Sexe.choices)
    date_naissance = models.DateField()
    ville = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    actif = models.BooleanField(default=True)

    def get_delai_jours(self):
        return 56 if self.sexe == self.Sexe.HOMME else 84

    def get_dernier_don(self):
        return self.dons.filter(valide=True).order_by('-date_don').first()

    def get_prochaine_date_eligibilite(self):
        dernier = self.get_dernier_don()
        if dernier:
            return dernier.date_don + timedelta(days=self.get_delai_jours())
        return None

    def est_eligible(self):
        prochaine = self.get_prochaine_date_eligibilite()
        if prochaine is None:
            return True
        return timezone.now().date() >= prochaine

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.groupe_sanguin})'


class Hopital(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hopital')
    nom = models.CharField(max_length=200)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    numero_agrement = models.CharField(max_length=100, unique=True)
    valide = models.BooleanField(default=False)

    def __str__(self):
        return self.nom


class DemandeUrgente(models.Model):
    class Statut(models.TextChoices):
        ACTIVE = 'active', 'Active'
        CLOTUREE = 'cloturee', 'Clôturée'
        SATISFAITE = 'satisfaite', 'Satisfaite'

    hopital = models.ForeignKey(Hopital, on_delete=models.CASCADE, related_name='demandes')
    groupe_sanguin = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    quantite = models.PositiveIntegerField(help_text='Nombre de poches')
    delai = models.DateField(help_text='Date limite')
    description = models.TextField(blank=True)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.ACTIVE)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.groupe_sanguin} — {self.hopital.nom} ({self.statut})'

    class Meta:
        ordering = ['-date_creation']


class Don(models.Model):
    donneur = models.ForeignKey(Donneur, on_delete=models.CASCADE, related_name='dons')
    hopital = models.ForeignKey(Hopital, on_delete=models.SET_NULL, null=True, related_name='dons_recus')
    date_don = models.DateField()
    notes = models.TextField(blank=True)
    valide = models.BooleanField(default=True)
    date_enregistrement = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Don de {self.donneur} le {self.date_don}'

    class Meta:
        ordering = ['-date_don']


class Campagne(models.Model):
    hopital = models.ForeignKey(Hopital, on_delete=models.CASCADE, related_name='campagnes')
    nom = models.CharField(max_length=200)
    date = models.DateField()
    lieu = models.CharField(max_length=200)
    groupes_cibles = models.CharField(max_length=100, help_text='Ex: A+,B+,O-')
    capacite_totale = models.PositiveIntegerField()
    capacite_par_creneau = models.PositiveIntegerField(default=10, help_text='Nombre max de donneurs par créneau horaire')
    description = models.TextField(blank=True)
    annulee = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)

    def places_restantes(self):
        return self.capacite_totale - self.inscriptions.count()

    def est_complete(self):
        return self.places_restantes() <= 0

    def get_groupes_list(self):
        return [g.strip() for g in self.groupes_cibles.split(',') if g.strip()]

    def __str__(self):
        return f'{self.nom} — {self.date}'

    class Meta:
        ordering = ['date']


class Inscription(models.Model):
    campagne = models.ForeignKey(Campagne, on_delete=models.CASCADE, related_name='inscriptions')
    donneur = models.ForeignKey(Donneur, on_delete=models.CASCADE, related_name='inscriptions')
    creneau_horaire = models.TimeField()
    date_inscription = models.DateTimeField(auto_now_add=True)
    present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('campagne', 'donneur')

    def __str__(self):
        return f'{self.donneur} → {self.campagne}'


class ReponseAppel(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        CONFIRME = 'confirme', 'Confirmé'
        ANNULE = 'annule', 'Annulé'

    demande = models.ForeignKey(DemandeUrgente, on_delete=models.CASCADE, related_name='reponses')
    donneur = models.ForeignKey(Donneur, on_delete=models.CASCADE, related_name='reponses')
    date_reponse = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.EN_ATTENTE)

    class Meta:
        unique_together = ('demande', 'donneur')

    def __str__(self):
        return f'{self.donneur} → {self.demande}'
