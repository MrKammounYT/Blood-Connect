from django.urls import path
from . import views

donor_urlpatterns = [
    path('dashboard/', views.donor_dashboard, name='dashboard'),
    path('demande/<int:pk>/respond/', views.respond_demande, name='respond_demande'),
    path('don/record/', views.record_don, name='record_don'),
]

hospital_urlpatterns = [
    path('dashboard/', views.hospital_dashboard, name='dashboard'),
    path('demande/create/', views.create_demande, name='create_demande'),
    path('demande/<int:pk>/edit/', views.edit_demande, name='edit_demande'),
    path('demande/<int:pk>/close/', views.close_demande, name='close_demande'),
    path('demande/<int:pk>/respondents/', views.demande_respondents, name='demande_respondents'),
    path('demandes/', views.demande_history, name='demande_history'),
]
