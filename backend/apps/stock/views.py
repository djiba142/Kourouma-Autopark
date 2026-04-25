from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Localisation, StockParLocalisation, MouvementStock, TransfertStock, TransfertItem
from .serializers import (
    LocalisationSerializer, StockParLocalisationSerializer,
    MouvementStockSerializer, TransfertStockSerializer
)
import uuid

class LocalisationViewSet(viewsets.ModelViewSet):
    queryset = Localisation.objects.filter(actif=True)
    serializer_class = LocalisationSerializer
    permission_classes = [permissions.IsAuthenticated]

class StockParLocalisationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockParLocalisation.objects.all()
    serializer_class = StockParLocalisationSerializer
    filterset_fields = ['produit', 'localisation', 'localisation__type']

from auth_users.permissions import IsBSGAdminOrMagasinier

class MouvementStockViewSet(viewsets.ModelViewSet):
    queryset = MouvementStock.objects.all()
    serializer_class = MouvementStockSerializer
    permission_classes = [permissions.IsAuthenticated, IsBSGAdminOrMagasinier]

    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)

class TransfertStockViewSet(viewsets.ModelViewSet):
    queryset = TransfertStock.objects.all()
    serializer_class = TransfertStockSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        ref = f"TRF-{uuid.uuid4().hex[:6].upper()}"
        transfert = serializer.save(cree_par=self.request.user, reference=ref)
        # Handle item creation from request data
        items_data = self.request.data.get('items', [])
        for item in items_data:
            TransfertItem.objects.create(
                transfert=transfert,
                produit_id=item['produit'],
                quantite_demandee=item['quantite']
            )

    @action(detail=True, methods=['post'])
    def expedier(self, request, pk=None):
        transfert = self.get_object()
        if transfert.statut != 'PROPOSE':
            return Response({"error": "Déjà expédié ou invalide"}, status=400)
            
        # 1. Deduct from provenance (MAGASIN)
        for item in transfert.items.all():
            MouvementStock.objects.create(
                produit=item.produit,
                localisation=transfert.provenance,
                type='SORTIE',
                quantite=item.quantite_demandee,
                reference_doc=transfert.reference,
                utilisateur=request.user,
                notes=f"Expédition transfert {transfert.reference}"
            )
            item.quantite_reelle = item.quantite_demandee
            item.save()
            
        transfert.statut = 'EXPEDIE'
        transfert.valide_par = request.user
        transfert.date_validation = timezone.now()
        transfert.save()
        return Response({"status": "Expédié vers destination"})

    @action(detail=True, methods=['post'])
    def recevoir(self, request, pk=None):
        transfert = self.get_object()
        if transfert.statut != 'EXPEDIE':
            return Response({"error": "Seulement possible après expédition"}, status=400)
            
        # 2. Add to destination (BOUTIQUE)
        for item in transfert.items.all():
            MouvementStock.objects.create(
                produit=item.produit,
                localisation=transfert.destination,
                type='ENTREE',
                quantite=item.quantite_reelle,
                reference_doc=transfert.reference,
                utilisateur=request.user,
                notes=f"Réception transfert {transfert.reference}"
            )
            
        transfert.statut = 'RECU'
        transfert.date_reception = timezone.now()
        transfert.save()
        return Response({"status": "Reçu et stock boutique mis à jour"})
