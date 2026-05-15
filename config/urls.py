from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/',  admin.site.urls),

    # ── Redirection Accueil vers Login (Logique 2) ────────────────────────
    path('',        lambda r: redirect('/login/')),
    path('',        include('web.urls', namespace='web')),
    path('manifest.json', lambda r: redirect(settings.STATIC_URL + 'web/manifest.json')),

    # ── API REST conservée (pour compatibilité / intégrations futures) ─────
    path('api/v1/auth/',       include('auth_users.urls')),
    path('api/v1/produits/',   include('produits.urls')),
    path('api/v1/stock/',      include('stock.urls')),
    path('api/v1/clients/',    include('clients.urls')),
    path('api/v1/commandes/',  include('commandes.urls')),
    path('api/v1/achats/',     include('achats.urls')),
    path('api/v1/finances/',   include('finances.urls')),
    path('api/v1/audit/',      include('audit.urls')),
    path('api/v1/dashboard/',  include('dashboard.urls')),
    path('api/v1/ia/',         include('ia.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
