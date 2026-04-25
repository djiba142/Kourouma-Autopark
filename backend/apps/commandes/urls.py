from rest_framework.routers import DefaultRouter
from .views import CommandeViewSet

router = DefaultRouter()
router.register('', CommandeViewSet, basename='commandes')

urlpatterns = router.urls
