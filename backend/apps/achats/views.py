from rest_framework import viewsets, decorators, response, status, permissions
from django.db import transaction
from django.utils import timezone
from .models import Fournisseur, CommandeAchat, LigneAchat
from .serializers import FournisseurSerializer, CommandeAchatSerializer
from stock.models import Localisation, StockParLocalisation, MouvementStock
from produits.models import Produit, HistoriquePrix
from auth_users.permissions import IsBSGAdminOrMagasinier

class FournisseurViewSet(viewsets.ModelViewSet):
    queryset = Fournisseur.objects.all()
    serializer_class = FournisseurSerializer
    permission_classes = [permissions.IsAuthenticated]

class CommandeAchatViewSet(viewsets.ModelViewSet):
    queryset = CommandeAchat.objects.all()
    serializer_class = CommandeAchatSerializer
    permission_classes = [permissions.IsAuthenticated, IsBSGAdminOrMagasinier]

    @transaction.atomic
    def perform_create(self, serializer):
        # Generate Reference
        now = timezone.now()
        timestamp = now.strftime('%y%m%d%H%M%S')
        reference = f"PO-{timestamp}"
        
        instance = serializer.save(reference=reference, cree_par=self.request.user)
        self._calculate_totals(instance)

    def _calculate_totals(self, instance):
        total_devise = sum(l.sous_total_devise for l in instance.lignes.all())
        instance.total_devise = total_devise
        instance.total_gnf = total_devise * instance.taux_change
        instance.save()

    @decorators.action(detail=True, methods=['post'])
    @transaction.atomic
    def recevoir(self, request, pk=None):
        po = self.get_object()
        if po.statut == 'RECUE':
            return response.Response({"error": "Cette commande est déjà reçue"}, status=400)
        
        # 1. Target Localisation (Magasin by default)
        magasin = Localisation.objects.filter(type='MAGASIN').first()
        if not magasin:
            return response.Response({"error": "Localisation 'MAGASIN' non trouvée"}, status=400)
            
        # 2. Process Lines and Stock
        for line in po.lignes.all():
            produit = line.produit
            
            # Log Movement (The signal synchro_stock_localisation will update stock automatically)
            MouvementStock.objects.create(
                produit=produit,
                localisation=magasin,
                type='ENTREE',
                quantite=line.quantite_pieces,
                utilisateur=request.user,
                reference_doc=po.reference,
                notes=f"Réception PO {po.reference} de {po.fournisseur.nom}"
            )
            
            # Update Product Price Snapshot (Strict traceability)
            # landed_cost_gnf = prix_unit_devise * taux
            landed_unit_gnf = (line.prix_unitaire_devise * po.taux_change) / produit.conversion_unit # convert carton price to piece price
            
            HistoriquePrix.objects.create(
                produit=produit,
                ancien_prix=produit.prix_achat,
                nouveau_prix=landed_unit_gnf,
                modifie_par=request.user
            )
            
            produit.prix_achat = landed_unit_gnf
            produit.prix_achat_devise = line.prix_unitaire_devise / produit.conversion_unit
            produit.achat_devise = po.devise
            produit.taux_change_achat = po.taux_change
            produit.save()

        # 3. Finalize PO Status
        po.statut = 'RECUE'
        po.date_reception_reelle = timezone.now()
        po.save()

        return response.Response({"status": "Marchandise reçue, stock Magasin mis à jour"})
