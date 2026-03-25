from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from core.urls import donor_urlpatterns, hospital_urlpatterns, admin_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('donor/', include((donor_urlpatterns, 'donor'))),
    path('hospital/', include((hospital_urlpatterns, 'hospital'))),
    path('bloodadmin/', include((admin_urlpatterns, 'admin_panel'))),
]
