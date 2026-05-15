from rest_framework import viewsets, filters, permissions
from .models import Client
from .serializers import ClientSerializer
from django_filters.rest_framework import DjangoFilterBackend

class ClientViewSet(viewsets.ModelViewSet):
    """
    Gestion des clients avec recherche par nom ou téléphone.
    """
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['actif', 'score_statut']
    search_fields = ['nom', 'telephone']
    ordering_fields = ['nom', 'date_creation', 'total_dette']
