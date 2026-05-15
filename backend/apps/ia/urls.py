from django.urls import path
from .views import (
    IAVentesAPIView, IAAnomaliesAPIView, 
    IARecommandationsAPIView, IARentabiliteAPIView,
    IADashboardAPIView
)

urlpatterns = [
    path('dashboard/', IADashboardAPIView.as_view(), name='api_ia_dashboard'),
    path('ventes/', IAVentesAPIView.as_view(), name='api_ia_ventes'),
    path('anomalies/', IAAnomaliesAPIView.as_view(), name='api_ia_anomalies'),
    path('recommandations/', IARecommandationsAPIView.as_view(), name='api_ia_recommandations'),
    path('rentabilite/', IARentabiliteAPIView.as_view(), name='api_ia_rentabilite'),
]
