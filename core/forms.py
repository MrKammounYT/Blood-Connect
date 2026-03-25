from django import forms
from .models import DemandeUrgente, Don, Campagne, Inscription, BLOOD_GROUPS


class DemandeUrgenteForm(forms.ModelForm):
    class Meta:
        model = DemandeUrgente
        fields = ('groupe_sanguin', 'quantite', 'delai', 'description')
        widgets = {
            'delai': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'groupe_sanguin': 'Groupe sanguin requis',
            'quantite': 'Quantité (poches)',
            'delai': 'Date limite',
            'description': 'Description',
        }


class DonForm(forms.ModelForm):
    class Meta:
        model = Don
        fields = ('hopital', 'date_don', 'notes')
        widgets = {
            'date_don': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'hopital': 'Établissement',
            'date_don': 'Date du don',
            'notes': 'Notes (optionnel)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Hopital
        self.fields['hopital'].queryset = Hopital.objects.filter(valide=True)


class CampagneForm(forms.ModelForm):
    groupes_cibles = forms.MultipleChoiceField(
        choices=BLOOD_GROUPS,
        widget=forms.CheckboxSelectMultiple,
        label='Groupes sanguins ciblés',
    )

    class Meta:
        model = Campagne
        fields = ('nom', 'date', 'lieu', 'groupes_cibles', 'capacite_totale', 'capacite_par_creneau', 'description')
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'nom': 'Nom de la campagne',
            'lieu': 'Lieu',
            'capacite_totale': 'Capacité totale (donneurs)',
            'capacite_par_creneau': 'Capacité par créneau',
            'description': 'Description (optionnel)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate multi-select from comma-separated string
        instance = kwargs.get('instance')
        if instance and instance.groupes_cibles:
            self.initial['groupes_cibles'] = instance.get_groupes_list()

    def clean_groupes_cibles(self):
        return ','.join(self.cleaned_data['groupes_cibles'])


class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        fields = ('creneau_horaire',)
        widgets = {'creneau_horaire': forms.TimeInput(attrs={'type': 'time'})}
        labels = {'creneau_horaire': 'Créneau horaire souhaité'}
