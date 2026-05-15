from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import (
    CommandeViewSet, 
    RechercheProduitView, 
    PanierView, 
    CalculRemiseView
)

router = DefaultRouter()
router.register('', CommandeViewSet, basename='commandes')

urlpatterns = [
    # Endpoints vente directe (panier + recherche)
    path('recherche-produit/', RechercheProduitView.as_view(), name='recherche_produit'),
    path('panier/', PanierView.as_view(), name='panier_add'),
    path('panier/<int:ligne_id>/', PanierView.as_view(), name='panier_remove'),
    path('calcul-remise/', CalculRemiseView.as_view(), name='calcul_remise'),
] + router.urls
