"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "status": "online",
        "message": "Bienvenue sur l'API BSG AutoParts Pro Max",
        "version": "1.0",
        "docs": "Endpoints disponibles sous /api/v1/"
    })

urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('auth_users.urls')),
    path('api/v1/produits/', include('produits.urls')),
    path('api/v1/stock/', include('stock.urls')),
    path('api/v1/clients/', include('clients.urls')),
    path('api/v1/commandes/', include('commandes.urls')),
    path('api/v1/achats/', include('achats.urls')),
    path('api/v1/finances/', include('finances.urls')),
    path('api/v1/audit/', include('audit.urls')),
    path('api/v1/dashboard/', include('dashboard.urls')),
    # Other apps will be added as needed
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
