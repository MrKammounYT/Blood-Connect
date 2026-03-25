from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User
from core.models import Donneur, Hopital


class DonneurRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label='Prénom')
    last_name = forms.CharField(max_length=100, label='Nom')
    email = forms.EmailField(label='Email')
    groupe_sanguin = forms.ChoiceField(choices=Donneur._meta.get_field('groupe_sanguin').choices, label='Groupe sanguin')
    sexe = forms.ChoiceField(choices=Donneur.Sexe.choices, label='Sexe')
    date_naissance = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), label='Date de naissance')
    ville = forms.CharField(max_length=100, label='Ville')
    telephone = forms.CharField(max_length=20, required=False, label='Téléphone')

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.DONNEUR
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Donneur.objects.create(
                user=user,
                groupe_sanguin=self.cleaned_data['groupe_sanguin'],
                sexe=self.cleaned_data['sexe'],
                date_naissance=self.cleaned_data['date_naissance'],
                ville=self.cleaned_data['ville'],
                telephone=self.cleaned_data.get('telephone', ''),
            )
        return user


class HopitalRegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Email')
    nom = forms.CharField(max_length=200, label="Nom de l'établissement")
    adresse = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Adresse')
    ville = forms.CharField(max_length=100, label='Ville')
    telephone = forms.CharField(max_length=20, required=False, label='Téléphone')
    numero_agrement = forms.CharField(max_length=100, label="Numéro d'agrément")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.HOPITAL
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Hopital.objects.create(
                user=user,
                nom=self.cleaned_data['nom'],
                adresse=self.cleaned_data['adresse'],
                ville=self.cleaned_data['ville'],
                telephone=self.cleaned_data.get('telephone', ''),
                numero_agrement=self.cleaned_data['numero_agrement'],
                valide=False,
            )
        return user


class DonneurProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=100, label='Prénom')
    last_name = forms.CharField(max_length=100, label='Nom')
    email = forms.EmailField(label='Email')

    class Meta:
        model = Donneur
        fields = ('groupe_sanguin', 'sexe', 'date_naissance', 'ville', 'telephone', 'actif')
        widgets = {'date_naissance': forms.DateInput(attrs={'type': 'date'})}
        labels = {
            'groupe_sanguin': 'Groupe sanguin',
            'date_naissance': 'Date de naissance',
            'actif': 'Compte actif (décocher pour signaler une indisponibilité temporaire)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save_user(self, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()


class HopitalProfileForm(forms.ModelForm):
    email = forms.EmailField(label='Email')

    class Meta:
        model = Hopital
        fields = ('nom', 'adresse', 'ville', 'telephone')
        labels = {
            'nom': "Nom de l'établissement",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['email'].initial = user.email

    def save_user(self, user):
        user.email = self.cleaned_data['email']
        user.save()
