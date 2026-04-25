from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LocalisationViewSet, StockParLocalisationViewSet,
    MouvementStockViewSet, TransfertStockViewSet
)

router = DefaultRouter()
router.register('localisations', LocalisationViewSet)
router.register('inventaire', StockParLocalisationViewSet)
router.register('mouvements', MouvementStockViewSet)
router.register('transferts', TransfertStockViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
