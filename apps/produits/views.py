from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Produit, Categorie, Marque, HistoriquePrix
from .serializers import ProduitSerializer, CategorieSerializer, MarqueSerializer, HistoriquePrixSerializer
from apps.auth_users.permissions import IsBSGAdmin

class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.all()
    serializer_class = CategorieSerializer
    permission_classes = [permissions.IsAuthenticated]

class MarqueViewSet(viewsets.ModelViewSet):
    queryset = Marque.objects.all()
    serializer_class = MarqueSerializer
    permission_classes = [permissions.IsAuthenticated]

class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.all()
    serializer_class = ProduitSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['categorie', 'marque_rel', 'actif']
    search_fields = ['nom', 'reference', 'code_barre']
    ordering_fields = ['nom', 'prix_vente', 'quantite', 'date_ajout']

    def perform_update(self, serializer):
        # Logic to track price history
        old_instance = self.get_object()
        new_prix = serializer.validated_data.get('prix_vente')
        
        # Security: Only Admin can change prices
        if new_prix and new_prix != old_instance.prix_vente:
            if not self.request.user.role == 'ADMIN':
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("Seul un Administrateur peut modifier les prix.")
            
            # Create History entry
            HistoriquePrix.objects.create(
                produit=old_instance,
                ancien_prix=old_instance.prix_vente,
                nouveau_prix=new_prix,
                modifie_par=self.request.user
            )
            
        serializer.save()

    @action(detail=False, methods=['get'], url_path='faible-stock')
    def faible_stock(self, request):
        """Returns products where quantity <= seuil_alerte"""
        # Using __lte for efficiency
        from django.db.models import F
        queryset = Produit.objects.filter(quantite__lte=F('seuil_alerte'), actif=True)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='historique-prix')
    def historique_prix(self, request, pk=None):
        """Returns the price history of a specific product"""
        produit = self.get_object()
        historique = HistoriquePrix.objects.filter(produit=produit)
        serializer = HistoriquePrixSerializer(historique, many=True)
        return Response(serializer.data)
