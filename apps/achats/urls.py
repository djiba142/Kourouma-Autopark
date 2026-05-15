from rest_framework.routers import DefaultRouter
from .views import FournisseurViewSet, CommandeAchatViewSet

router = DefaultRouter()
router.register('fournisseurs', FournisseurViewSet, basename='fournisseurs')
router.register('commandes', CommandeAchatViewSet, basename='achats')

urlpatterns = router.urls
