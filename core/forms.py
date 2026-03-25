from django import forms
from .models import DemandeUrgente, Don, BLOOD_GROUPS


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
