"""
=================================================================
 DASHBOARD API — Module Finance Central
 
 Vue globale du système ERP :
 - Total ventes (commandes livrées)
 - Total dépenses
 - Profit = ventes - dépenses
 - Stock global
 - Dettes clients
 - Top 5 produits vendus
 - 10 dernières commandes
=================================================================
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Count, F, Q
from commandes.models import Commande, LigneCommande, Paiement
from finances.models import Depense, JournalFinancier
from stock.models import StockParLocalisation
from clients.models import Client


class DashboardAPIView(APIView):
    """Finance Central — Vue globale du système"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # ── VENTES (Statistiques) ──
        commandes_livrees = Commande.objects.filter(statut='LIVREE')
        total_ventes = commandes_livrees.aggregate(
            total=Sum('total_ttc')
        )['total'] or 0

        # ── COMPTABILITÉ (JOURNAL FINANCIER) ──
        # Le profit est maintenant calculé sur la base de la réalité du journal
        entrees = JournalFinancier.objects.filter(type_flux='ENTREE').aggregate(total=Sum('montant_gnf'))['total'] or 0
        sorties = JournalFinancier.objects.filter(type_flux='SORTIE').aggregate(total=Sum('montant_gnf'))['total'] or 0
        
        profit = float(entrees) - float(sorties)

        # ── DÉPENSES ──
        total_depenses = sorties # Dans le journal, toutes les sorties sont des dépenses/achats

        # ── STOCK GLOBAL ──
        stock_global = StockParLocalisation.objects.aggregate(
            total=Sum('quantite')
        )['total'] or 0

        # ── DETTES CLIENTS ──
        clients = Client.objects.filter(actif=True)
        dettes_clients = sum(
            max(0, float(c.total_dette)) for c in clients
        )

        # ── TOP 5 PRODUITS VENDUS ──
        top_produits = (
            LigneCommande.objects
            .values('produit__nom', 'produit__reference')
            .annotate(total_vendu=Sum('quantite'))
            .order_by('-total_vendu')[:5]
        )

        # ── 10 DERNIÈRES COMMANDES ──
        dernieres_commandes = (
            Commande.objects
            .select_related('client')
            .order_by('-date_creation')[:10]
            .values(
                'id', 'numero', 'client__nom', 'total_ttc',
                'statut', 'statut_paiement', 'date_creation'
            )
        )

        # ── 10 DERNIERS MOUVEMENTS JOURNAL ──
        journal_recent = (
            JournalFinancier.objects
            .order_by('-created_at')[:10]
            .values(
                'numero', 'type_operation', 'reference_doc', 
                'montant_gnf', 'type_flux', 'date'
            )
        )

        # ── COMPTEURS ──
        nb_commandes_en_cours = Commande.objects.filter(
            statut__in=['EN_ATTENTE', 'VALIDEE', 'EN_PREPARATION', 'PRETE']
        ).count()

        nb_produits_alerte = StockParLocalisation.objects.filter(
            quantite__lte=F('produit__seuil_alerte')
        ).count()

        return Response({
            'total_ventes': total_ventes,
            'total_paiements': entrees,
            'total_depenses': sorties,
            'profit': profit,
            'stock_global': stock_global,
            'dettes_clients': dettes_clients,
            'nb_commandes_en_cours': nb_commandes_en_cours,
            'nb_produits_alerte': nb_produits_alerte,
            'top_produits': list(top_produits),
            'dernieres_commandes': list(dernieres_commandes),
            'journal_recent': list(journal_recent),
        })
