from django.contrib import admin
from django.urls import path, include

from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # <--- C'est CETTE vue officielle qu'il faut utiliser
]

urlpatterns += i18n_patterns(
    path('', include('principal.urls')),
)