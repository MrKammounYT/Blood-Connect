from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/donneur/', views.register_donneur, name='register_donneur'),
    path('register/hopital/', views.register_hopital, name='register_hopital'),
    path('profile/donneur/', views.profile_donneur, name='profile_donneur'),
    path('profile/hopital/', views.profile_hopital, name='profile_hopital'),
]
