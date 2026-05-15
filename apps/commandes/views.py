from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.http import FileResponse
from rest_framework import views, status, response, permissions, filters
from .models import Commande, LigneCommande, Paiement
from .serializers import CommandeSerializer, LigneCommandeSerializer, PaiementSerializer, PanierSerializer
from .pdf_utils import generer_facture_pdf
from produits.models import Produit
from stock.models import MouvementStock, Localisation, StockParLocalisation
from datetime import datetime
from rest_framework import viewsets, decorators

class CommandeViewSet(viewsets.ModelViewSet):
    queryset = Commande.objects.all()
    serializer_class = CommandeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['numero', 'client__nom', 'client__email']
    ordering_fields = ['date_creation', 'total_ttc', 'statut']
    ordering = ['-date_creation']

    def get_queryset(self):
        """Filtres avancés: statut, date, client, type_vente"""
        queryset = Commande.objects.all()
        
        # Filtre statut
        statut = self.request.query_params.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        # Filtre type de vente
        type_vente = self.request.query_params.get('type_vente')
        if type_vente:
            queryset = queryset.filter(type_vente=type_vente)
        
        # Filtre client
        client_id = self.request.query_params.get('client')
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filtres date
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        if date_debut:
            queryset = queryset.filter(date_creation__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_creation__lte=date_fin)
        
        # Filtre statut paiement
        statut_paiement = self.request.query_params.get('statut_paiement')
        if statut_paiement:
            queryset = queryset.filter(statut_paiement=statut_paiement)
        
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

    @decorators.action(detail=True, methods=['get'])
    def generer_facture(self, request, pk=None):
        """Génère et retourne le PDF de la facture"""
        commande = self.get_object()
        
        try:
            pdf_buffer = generer_facture_pdf(commande)
            filename = f"Facture_{commande.numero}_{datetime.now().strftime('%Y%m%d')}.pdf"
            
            return FileResponse(
                pdf_buffer,
                as_attachment=True,
                filename=filename,
                content_type='application/pdf'
            )
        except Exception as e:
            return response.Response(
                {"error": f"Erreur génération PDF: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @decorators.action(detail=True, methods=['post'])
    def livrer(self, request, pk=None):
        """Marquer la commande comme livrée"""
        commande = self.get_object()
        if commande.statut != 'EXPEDIEE':
            return response.Response(
                {"error": "La commande doit être expédiée avant livraison"}, status=400
            )
        
        commande.statut = 'LIVREE'
        commande.save()
        return response.Response({"status": "Commande livrée"})

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


# ════════════════════════════════════════════════════════════════════════════════════
# ENDPOINTS VENTE DIRECTE: Recherche Produit + Panier Dynamique
# ════════════════════════════════════════════════════════════════════════════════════

class RechercheProduitView(views.APIView):
    """Recherche produit live pour vente directe (HTMX)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Recherche produit par nom ou référence"""
        query = request.query_params.get('q', '').strip()
        localisation_id = request.query_params.get('localisation')
        
        if len(query) < 2:
            return response.Response(
                {"results": [], "message": "Minimum 2 caractères pour rechercher"}
            )
        
        # Recherche dans nom, description, référence
        produits = Produit.objects.filter(
            Q(nom__icontains=query) | 
            Q(reference__icontains=query) |
            Q(description__icontains=query)
        )[:20]
        
        # Ajouter les informations de stock
        resultats = []
        for produit in produits:
            if localisation_id:
                stock = StockParLocalisation.objects.filter(
                    produit=produit, 
                    localisation_id=localisation_id
                ).first()
                quantite_dispo = stock.quantite if stock else 0
            else:
                quantite_dispo = sum(
                    s.quantite for s in StockParLocalisation.objects.filter(produit=produit)
                )
            
            resultats.append({
                'id': produit.id,
                'nom': produit.nom,
                'reference': produit.reference,
                'prix_unitaire': float(produit.prix_vente),
                'quantite_dispo': quantite_dispo,
                'unite': produit.unite,
                'image_url': produit.image.url if produit.image else None,
            })
        
        return response.Response({"results": resultats})


class PanierView(views.APIView):
    """Gestion panier dynamique (ajouter/retirer/maj articles)"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Ajouter ou mettre à jour une ligne de commande au panier"""
        commande_id = request.data.get('commande_id')
        produit_id = request.data.get('produit_id')
        quantite = int(request.data.get('quantite', 1))
        
        if quantite <= 0:
            return response.Response(
                {"error": "Quantité invalide"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            commande = Commande.objects.get(id=commande_id)
            produit = Produit.objects.get(id=produit_id)
        except Commande.DoesNotExist:
            return response.Response(
                {"error": "Commande non trouvée"}, status=status.HTTP_404_NOT_FOUND
            )
        except Produit.DoesNotExist:
            return response.Response(
                {"error": "Produit non trouvé"}, status=status.HTTP_404_NOT_FOUND
            )
        
        # Vérifier stock disponible
        localisation = commande.localisation or Localisation.objects.filter(
            nom__icontains="BOUTIQUE"
        ).first()
        stock = StockParLocalisation.objects.filter(
            produit=produit, 
            localisation=localisation
        ).first()
        
        if not stock or stock.quantite < quantite:
            disponible = stock.quantite if stock else 0
            return response.Response(
                {"error": f"Stock insuffisant. Disponible: {disponible}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Ajouter ou mettre à jour la ligne
        ligne, created = LigneCommande.objects.get_or_create(
            commande=commande,
            produit=produit,
            defaults={
                'quantite': quantite,
                'prix_unitaire': produit.prix_vente
            }
        )
        
        if not created:
            ligne.quantite = quantite
            ligne.prix_unitaire = produit.prix_vente
            ligne.save()
        
        # Recalculer totaux
        self._calculer_totaux_commande(commande)
        
        return response.Response({
            "status": "Article ajouté au panier",
            "ligne": LigneCommandeSerializer(ligne).data,
            "commande": CommandeSerializer(commande).data
        })
    
    def delete(self, request, ligne_id=None):
        """Retirer un article du panier"""
        try:
            ligne = LigneCommande.objects.get(id=ligne_id)
            commande = ligne.commande
            ligne.delete()
            
            # Recalculer totaux
            self._calculer_totaux_commande(commande)
            
            return response.Response({
                "status": "Article retiré",
                "commande": CommandeSerializer(commande).data
            })
        except LigneCommande.DoesNotExist:
            return response.Response(
                {"error": "Article non trouvé"}, status=status.HTTP_404_NOT_FOUND
            )
    
    def _calculer_totaux_commande(self, commande):
        """Recalcule les totaux HT et TTC"""
        total_ht = sum(
            float(l.quantite) * float(l.prix_unitaire) 
            for l in commande.lignes.all()
        )
        commande.total_ht = total_ht
        
        if commande.type_remise == 'POURCENT':
            commande.total_ttc = float(total_ht) * (1 - float(commande.remise) / 100)
        else:
            commande.total_ttc = float(total_ht) - float(commande.remise)
        
        commande.save()


class CalculRemiseView(views.APIView):
    """Calculer remise dynamiquement"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Appliquer/calculer remise"""
        commande_id = request.data.get('commande_id')
        type_remise = request.data.get('type_remise', 'POURCENT')  # POURCENT ou FIXE
        valeur_remise = float(request.data.get('valeur_remise', 0))
        
        try:
            commande = Commande.objects.get(id=commande_id)
        except Commande.DoesNotExist:
            return response.Response(
                {"error": "Commande non trouvée"}, status=status.HTTP_404_NOT_FOUND
            )
        
        commande.type_remise = type_remise
        commande.remise = valeur_remise
        
        # Recalculer totaux
        total_ht = sum(
            float(l.quantite) * float(l.prix_unitaire) 
            for l in commande.lignes.all()
        )
        
        if type_remise == 'POURCENT':
            if valeur_remise < 0 or valeur_remise > 100:
                return response.Response(
                    {"error": "Pourcentage doit être entre 0 et 100"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            commande.total_ttc = float(total_ht) * (1 - float(valeur_remise) / 100)
        else:  # FIXE
            if valeur_remise > total_ht:
                return response.Response(
                    {"error": "Remise ne peut pas dépasser le total HT"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            commande.total_ttc = float(total_ht) - float(valeur_remise)
        
        commande.save()
        
        return response.Response({
            "status": "Remise appliquée",
            "total_ht": float(commande.total_ht),
            "remise": float(commande.remise),
            "total_ttc": float(commande.total_ttc)
        })
