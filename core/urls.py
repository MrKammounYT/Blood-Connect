from django.urls import path
from . import views

app_name_donor = 'donor'
app_name_hospital = 'hospital'

donor_urlpatterns = [
    path('dashboard/', views.donor_dashboard, name='dashboard'),
]

hospital_urlpatterns = [
    path('dashboard/', views.hospital_dashboard, name='dashboard'),
]
