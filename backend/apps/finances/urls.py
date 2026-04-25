from rest_framework.routers import DefaultRouter
from .views import (CategorieDepenseViewSet, DepenseViewSet, 
                    CompteComptableViewSet, JournalFinancierViewSet, EcritureComptableViewSet)

router = DefaultRouter()
router.register('categories', CategorieDepenseViewSet, basename='categories-depenses')
router.register('comptes', CompteComptableViewSet, basename='comptes-comptables')
router.register('journal', JournalFinancierViewSet, basename='journal-financier')
router.register('ecritures', EcritureComptableViewSet, basename='ecritures-comptables')
router.register('', DepenseViewSet, basename='depenses')

urlpatterns = router.urls
