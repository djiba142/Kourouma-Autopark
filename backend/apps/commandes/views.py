from django.db import transaction
from django.utils import timezone
from rest_framework import views, status, response, permissions
from .models import Commande, LigneCommande, Paiement
from .serializers import CommandeSerializer
from produits.models import Produit
from stock.models import MouvementStock
from datetime import datetime

from rest_framework import viewsets, decorators
from .serializers import CommandeSerializer, LigneCommandeSerializer, PaiementSerializer
from stock.models import Localisation, StockParLocalisation, MouvementStock

class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.all()
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Allow filtering by status and type
        queryset = Commande.objects.all()
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        return queryset

    @transaction.atomic
    def perform_create(self, serializer):
        # Generate Professional Numero
        now = datetime.now()
        timestamp = now.strftime('%y%m%d%H%M%S')
        numero = f"BSG-{timestamp}"
        
        # Initial status for direct sales vs orders
        type_vente = self.request.data.get('type_vente', 'COMMANDE')
        statut = 'VALIDEE' if type_vente == 'VENTE_DIRECTE' else 'EN_ATTENTE'
        
        instance = serializer.save(
            numero=numero, 
            cree_par=self.request.user,
            statut=statut
        )
        
        # Handle Lines and Stock for Direct Sales
        try:
            if type_vente == 'VENTE_DIRECTE':
                self._process_immediate_stock(instance)
        except Exception as e:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": str(e)})
        
        self._calculate_totals(instance)

        # Credit Limit Check
        client = instance.client
        if client and client.limite_credit > 0:
            current_debt = client.total_dette
            if current_debt + instance.total_ttc > client.limite_credit:
                raise Exception(
                    f"Action Bloquée : Limite de crédit dépassée ({client.limite_credit} GNF). "
                    f"Dette actuelle: {current_debt}, Nouvelle commande: {instance.total_ttc}"
                )

    def _calculate_totals(self, instance):
        total_ht = sum(l.sous_total for l in instance.lignes.all())
        instance.total_ht = total_ht
        
        if instance.type_remise == 'POURCENT':
            instance.total_ttc = float(total_ht) * (1 - float(instance.remise) / 100)
        else:
            instance.total_ttc = float(total_ht) - float(instance.remise)
            
        instance.save()

    def _process_immediate_stock(self, instance):
        loc = instance.localisation or Localisation.objects.filter(nom__icontains="BOUTIQUE").first()
        for line in instance.lignes.all():
            stock_item, _ = StockParLocalisation.objects.get_or_create(produit=line.produit, localisation=loc)
            if stock_item.quantite < line.quantite:
                raise Exception(f"Stock insuffisant à {loc.nom} pour {line.produit.nom}")
            
            MouvementStock.objects.create(
                produit=line.produit,
                localisation=loc,
                type='SORTIE',
                quantite=line.quantite,
                reference_doc=instance.numero,
                utilisateur=self.request.user,
                notes=f"Vente directe {instance.numero}"
            )

    @decorators.action(detail=True, methods=['post'])
    @transaction.atomic
    def valider(self, request, pk=None):
        commande = self.get_object()
        if commande.statut != 'EN_ATTENTE':
            return response.Response({"error": "La commande doit être en attente"}, status=400)
        
        try:
            self._process_immediate_stock(commande)
            commande.statut = 'VALIDEE'
            commande.date_validation = timezone.now()
            commande.save()
            return response.Response({"status": "Commande validée et stock réservé"})
        except Exception as e:
            return response.Response({"error": str(e)}, status=400)

    @decorators.action(detail=True, methods=['post'])
    def preparer(self, request, pk=None):
        commande = self.get_object()
        commande.statut = 'EN_PREPARATION'
        commande.prepare_par = request.user
        commande.save()
        return response.Response({"status": "Préparation commencée"})

    @decorators.action(detail=True, methods=['post'])
    def expedier(self, request, pk=None):
        commande = self.get_object()
        commande.statut = 'EXPEDIEE'
        commande.date_expedition = timezone.now()
        commande.save()
        return response.Response({"status": "Commande expédiée"})

    @decorators.action(detail=True, methods=['post'])
    @transaction.atomic
    def annuler(self, request, pk=None):
        commande = self.get_object()
        if commande.statut in ['EN_ATTENTE', 'VALIDEE', 'EN_PREPARATION']:
            # Restore stock if it was already deducted
            if commande.statut != 'EN_ATTENTE':
                loc = commande.localisation or Localisation.objects.filter(nom__icontains="BOUTIQUE").first()
                for line in commande.lignes.all():
                    MouvementStock.objects.create(
                        produit=line.produit,
                        localisation=loc,
                        type='ENTREE',
                        quantite=line.quantite,
                        reference_doc=commande.numero,
                        utilisateur=request.user,
                        notes=f"Annulation commande {commande.numero}"
                    )
            
            commande.statut = 'ANNULEE'
            commande.save()
            return response.Response({"status": "Commande annulée et stock restauré"})
        
        return response.Response({"error": "Impossible d'annuler une commande déjà livrée"}, status=400)

    @decorators.action(detail=True, methods=['post'])
    @transaction.atomic
    def paiement(self, request, pk=None):
        commande = self.get_object()
        montant = float(request.data.get('montant', 0))
        
        # ── VALIDATION: montant positif ──
        if montant <= 0:
            return response.Response(
                {"error": "Le montant du paiement doit être positif"}, status=400
            )
        
        # ── VALIDATION: paiement <= reste à payer ──
        total_paye_avant = sum(float(p.montant) for p in commande.paiements.all())
        reste = float(commande.total_ttc) - total_paye_avant
        if montant > reste:
            return response.Response(
                {"error": f"Montant supérieur au reste à payer ({reste} GNF)"}, status=400
            )
        
        Paiement.objects.create(
            commande=commande,
            montant=montant,
            mode_paiement=request.data.get('mode_paiement', 'CASH'),
            reference_transaction=request.data.get('reference_transaction'),
            enregistre_par=request.user
        )
        
        # Update Payment Status
        total_paye = total_paye_avant + montant
        if total_paye >= float(commande.total_ttc):
            commande.statut_paiement = 'PAYE'
        elif total_paye > 0:
            commande.statut_paiement = 'PARTIEL'
        
        commande.save()
        return response.Response({"status": "Paiement enregistré"})
