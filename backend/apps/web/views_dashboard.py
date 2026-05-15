"""
web/views_dashboard.py
Vue principale avec KPIs croisés (Ventes, Stock, Finances)
Adaptée selon le rôle de l'utilisateur.
"""
from django.shortcuts import render, redirect
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDay
from django.utils import timezone
import datetime
from web.middleware import login_required_web


@login_required_web
def dashboard_view(request):
    role = request.user.role
    ctx  = {'title': 'Tableau de bord', 'nb_alertes_stock': 0, 'nb_ruptures': 0}

    try:
        from commandes.models import Commande
        from finances.models import JournalFinancier
        from produits.models import Produit
        from stock.models import StockParLocalisation
        from clients.models import Client

        # ── KPIs communs ──────────────────────────────────────────────────────
        ctx['nb_commandes_jour'] = Commande.objects.filter(
            date_creation__date=datetime.date.today()
        ).count()

        # ── KPIs Ventes / Finances (Admin & Employé) ──────────────────────────
        if role in ('ADMIN', 'EMPLOYE'):
            debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0)
            
            # Encaissements du mois
            ctx['total_paiements_mois'] = JournalFinancier.objects.filter(
                type_flux='ENTREE',
                created_at__gte=debut_mois
            ).aggregate(t=Sum('montant_gnf'))['t'] or 0

            # Dépenses du mois
            ctx['total_depenses_mois'] = JournalFinancier.objects.filter(
                type_flux='SORTIE',
                created_at__gte=debut_mois
            ).aggregate(t=Sum('montant_gnf'))['t'] or 0

            ctx['profit_mois'] = ctx['total_paiements_mois'] - ctx['total_depenses_mois']

            # Dernières commandes
            ctx['commandes_recentes'] = Commande.objects.select_related(
                'client', 'cree_par'
            ).order_by('-date_creation')[:8]

            # ── DONNÉES GRAPHIC (15 derniers jours) ───────────────────────────
            fin_graph = timezone.now()
            debut_graph = fin_graph - datetime.timedelta(days=14)
            
            journal_graph = JournalFinancier.objects.filter(
                created_at__gte=debut_graph
            ).annotate(day=TruncDay('created_at')).values('day', 'type_flux').annotate(total=Sum('montant_gnf')).order_by('day')

            days = [(debut_graph + datetime.timedelta(days=i)).date() for i in range(15)]
            sales_per_day = {day: 0 for day in days}
            expenses_per_day = {day: 0 for day in days}

            for entry in journal_graph:
                d = entry['day'].date()
                if d in sales_per_day:
                    if entry['type_flux'] == 'ENTREE':
                        sales_per_day[d] = float(entry['total'])
                    else:
                        expenses_per_day[d] = float(entry['total'])

            import json
            ctx['chart_labels'] = json.dumps([d.strftime('%d/%m') for d in days])
            ctx['chart_sales'] = json.dumps([sales_per_day[d] for d in days])
            ctx['chart_expenses'] = json.dumps([expenses_per_day[d] for d in days])

        # ── KPIs Stock (Admin & Magasinier) ──────────────────────────────────
        if role in ('ADMIN', 'MAGASINIER'):
            from django.db.models.functions import Coalesce
            
            ctx['nb_alertes_stock'] = Produit.objects.filter(
                actif=True
            ).annotate(total_qty=Coalesce(Sum('stocks_locations__quantite'), 0)).filter(total_qty__lte=F('seuil_alerte')).count()
            
            ctx['nb_ruptures'] = Produit.objects.filter(
                actif=True
            ).annotate(total_qty=Coalesce(Sum('stocks_locations__quantite'), 0)).filter(total_qty__lte=0).count()

            # Alertes critiques pour le sidebar
            ctx['produits_alerte'] = Produit.objects.filter(
                actif=True
            ).annotate(total_qty=Coalesce(Sum('stocks_locations__quantite'), 0)).filter(total_qty__lte=F('seuil_alerte')).order_by('total_qty')[:5]


        # ── KPIs spécifiques Admin ────────────────────────────────────────────
        if role == 'ADMIN':
            # Calcul de la dette totale (Total Commandes - Total Paiements)
            from commandes.models import Commande, Paiement
            total_ttc = Commande.objects.filter(statut='LIVREE').aggregate(t=Sum('total_ttc'))['t'] or 0
            total_paye = Paiement.objects.aggregate(t=Sum('montant'))['t'] or 0
            ctx['total_dettes'] = total_ttc - total_paye
            
            ctx['journal_recent'] = JournalFinancier.objects.order_by('-created_at')[:10]
            
            # Pour les top débiteurs, on doit faire un calcul par client
            # Comme on ne peut pas sommer la propriété, on va prendre les clients actifs
            # et filtrer en Python (pour un dashboard, c'est acceptable si peu de clients)
            all_clients = list(Client.objects.filter(actif=True))
            clients_avec_dette = [c for c in all_clients if c.total_dette > 0]
            ctx['top_debiteurs'] = sorted(clients_avec_dette, key=lambda x: x.total_dette, reverse=True)[:5]

    except Exception as e:
        print(f"Dashboard error: {e}")

    return render(request, 'web/dashboard/dashboard.html', ctx)

