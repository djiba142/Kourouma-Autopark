from rest_framework import viewsets, permissions, response, decorators, mixins
from django.db.models import Sum
from .models import CategorieDepense, Depense, CompteComptable, JournalFinancier, EcritureComptable
from .serializers import (CategorieDepenseSerializer, DepenseSerializer, 
                          CompteComptableSerializer, JournalFinancierSerializer, EcritureComptableSerializer)

class CategorieDepenseViewSet(viewsets.ModelViewSet):
    queryset = CategorieDepense.objects.all()
    serializer_class = CategorieDepenseSerializer
    permission_classes = [permissions.IsAuthenticated]

class DepenseViewSet(mixins.CreateModelMixin,
                     mixins.ListModelMixin,
                     mixins.RetrieveModelMixin,
                     viewsets.GenericViewSet):
    """Dépenses sont IMMUTABLES : création + lecture uniquement. Pas de PUT/PATCH/DELETE."""
    queryset = Depense.objects.all()
    serializer_class = DepenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        queryset = Depense.objects.all()
        
        # Filter personal expenses: only ADMIN can see them
        if user.role != 'ADMIN':
            queryset = queryset.exclude(type_depense='PERSONNEL')
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user)

    @decorators.action(detail=False, methods=['get'])
    def statistiques(self, request):
        queryset = self.get_queryset()
        
        total_gnf = queryset.aggregate(total=Sum('montant_gnf'))['total'] or 0
        par_categorie = queryset.values('categorie__nom').annotate(total=Sum('montant_gnf'))
        par_type = queryset.values('type_depense').annotate(total=Sum('montant_gnf'))
        
        return response.Response({
            'total_gnf': total_gnf,
            'par_categorie': par_categorie,
            'par_type': par_type
        })

class CompteComptableViewSet(viewsets.ModelViewSet):
    queryset = CompteComptable.objects.all()
    serializer_class = CompteComptableSerializer
    permission_classes = [permissions.IsAuthenticated]

class JournalFinancierViewSet(viewsets.ReadOnlyModelViewSet):
    """Journal est en LECTURE SEULE via API pour garantir l'immutabilité."""
    queryset = JournalFinancier.objects.all()
    serializer_class = JournalFinancierSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['type_operation', 'type_flux', 'devise']

class EcritureComptableViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EcritureComptable.objects.all()
    serializer_class = EcritureComptableSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['compte', 'journal']
