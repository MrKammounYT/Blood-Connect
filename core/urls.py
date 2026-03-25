from django.urls import path
from . import views

admin_urlpatterns = [
    path('', views.admin_dashboard, name='dashboard'),
    path('hospitals/', views.admin_hospitals, name='hospitals'),
    path('hospitals/<int:pk>/validate/', views.admin_validate_hospital, name='validate_hospital'),
    path('hospitals/<int:pk>/reject/', views.admin_reject_hospital, name='reject_hospital'),
    path('demandes/', views.admin_demandes_map, name='demandes_map'),
    path('export/donors/', views.admin_export_donors, name='export_donors'),
]

donor_urlpatterns = [
    path('dashboard/', views.donor_dashboard, name='dashboard'),
    path('demande/<int:pk>/respond/', views.respond_demande, name='respond_demande'),
    path('don/record/', views.record_don, name='record_don'),
    path('campagnes/', views.donor_campagnes, name='campagnes'),
    path('campagnes/<int:pk>/register/', views.register_campagne, name='register_campagne'),
]

hospital_urlpatterns = [
    path('dashboard/', views.hospital_dashboard, name='dashboard'),
    path('demande/create/', views.create_demande, name='create_demande'),
    path('demande/<int:pk>/edit/', views.edit_demande, name='edit_demande'),
    path('demande/<int:pk>/close/', views.close_demande, name='close_demande'),
    path('demande/<int:pk>/delete/', views.delete_demande, name='delete_demande'),
    path('demande/<int:pk>/respondents/', views.demande_respondents, name='demande_respondents'),
    path('demandes/', views.demande_history, name='demande_history'),
    path('campagnes/', views.campagne_list, name='campagne_list'),
    path('campagnes/create/', views.create_campagne, name='create_campagne'),
    path('campagnes/<int:pk>/edit/', views.edit_campagne, name='edit_campagne'),
    path('campagnes/<int:pk>/cancel/', views.cancel_campagne, name='cancel_campagne'),
    path('campagnes/<int:pk>/attendees/', views.campagne_attendees, name='campagne_attendees'),
]
