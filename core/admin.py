from django.contrib import admin
from .models import Donneur, Hopital, DemandeUrgente, Don, Campagne, Inscription, ReponseAppel


@admin.register(Donneur)
class DonneurAdmin(admin.ModelAdmin):
    list_display = ('user', 'groupe_sanguin', 'sexe', 'ville', 'actif', 'est_eligible')
    list_filter = ('groupe_sanguin', 'sexe', 'actif', 'ville')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'ville')


@admin.register(Hopital)
class HopitalAdmin(admin.ModelAdmin):
    list_display = ('nom', 'ville', 'numero_agrement', 'valide')
    list_filter = ('valide', 'ville')
    search_fields = ('nom', 'ville', 'numero_agrement')
    actions = ['valider_hopitaux']

    @admin.action(description='Valider les hôpitaux sélectionnés')
    def valider_hopitaux(self, request, queryset):
        queryset.update(valide=True)


@admin.register(DemandeUrgente)
class DemandeUrgenteAdmin(admin.ModelAdmin):
    list_display = ('hopital', 'groupe_sanguin', 'quantite', 'delai', 'statut', 'date_creation')
    list_filter = ('statut', 'groupe_sanguin')
    search_fields = ('hopital__nom',)


@admin.register(Don)
class DonAdmin(admin.ModelAdmin):
    list_display = ('donneur', 'hopital', 'date_don', 'valide')
    list_filter = ('valide', 'date_don')
    search_fields = ('donneur__user__username', 'hopital__nom')


@admin.register(Campagne)
class CampagneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'hopital', 'date', 'lieu', 'capacite_totale', 'places_restantes')
    list_filter = ('date', 'hopital')
    search_fields = ('nom', 'lieu', 'hopital__nom')


@admin.register(Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('donneur', 'campagne', 'creneau_horaire', 'present')
    list_filter = ('present', 'campagne')


@admin.register(ReponseAppel)
class ReponseAppelAdmin(admin.ModelAdmin):
    list_display = ('donneur', 'demande', 'statut', 'date_reponse')
    list_filter = ('statut',)
