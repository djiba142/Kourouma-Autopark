"""
web/views_commandes.py
Gestion des ventes : liste, détail, workflow et Vente Directe (HTMX).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import datetime

from web.middleware import employe_or_admin, login_required_web
from commandes.models import Commande, LigneCommande, Paiement
from produits.models import Produit
from clients.models import Client
from stock.models import Localisation, StockParLocalisation, MouvementStock


@login_required_web
def commandes_liste(request):
    qs = Commande.objects.select_related('client', 'cree_par').order_by('-date_creation')

    # Filtres
    statut = request.GET.get('statut')
    if statut: qs = qs.filter(statut=statut)
    
    search = request.GET.get('q')
    if search:
        qs = qs.filter(numero__icontains=search) | qs.filter(client__nom__icontains=search)

    return render(request, 'web/commandes/liste.html', {
        'title': 'Commandes',
        'commandes': qs[:100],
        'statuts': Commande.STATUTS,
        'filtre_statut': statut,
        'search': search,
    })


@login_required_web
def commande_detail(request, pk):
    cmd = get_object_or_404(Commande, pk=pk)
    lignes = cmd.lignes.select_related('produit').all()
    paiements = cmd.paiements.all()
    
    return render(request, 'web/commandes/detail.html', {
        'title': f'Commande {cmd.numero}',
        'cmd': cmd,
        'lignes': lignes,
        'paiements': paiements,
        'reste': cmd.reste_a_payer,
    })


@employe_or_admin
@transaction.atomic
def vente_directe(request):
    if request.method == 'GET':
        return render(request, 'web/commandes/vente_directe.html', {
            'title': 'Vente directe',
            'clients': Client.objects.filter(actif=True).order_by('nom'),
        })

    # Traitement POST : Création d'une vente comptoir immédiate
    try:
        client_id     = request.POST.get('client_id')
        produits_ids  = request.POST.getlist('produit_id')
        quantites     = request.POST.getlist('quantite')
        prix_unitaires = request.POST.getlist('prix_unitaire')
        
        montant_paye  = float(request.POST.get('montant_paye', 0))
        mode_paiement = request.POST.get('mode_paiement', 'CASH')

        if not produits_ids:
            messages.error(request, "Le panier est vide.")
            return redirect('web:vente_directe')

        # 1. Créer la commande
        loc_boutique = Localisation.objects.get(type='BOUTIQUE') # Localisation par défaut
        cmd = Commande.objects.create(
            numero=f"VNT-{datetime.now().strftime('%y%m%d-%H%M%S')}",
            client_id=client_id if client_id else None,
            statut='VALIDEE',
            type_vente='VENTE_DIRECTE',
            localisation=loc_boutique,
            cree_par=request.user
        )

        total_ht = 0
        # 2. Créer les lignes et déduire le stock
        for p_id, qte, pu in zip(produits_ids, quantites, prix_unitaires):
            produit = Produit.objects.get(pk=p_id)
            qte = int(qte)
            pu  = float(pu)
            st  = qte * pu
            total_ht += st
            
            LigneCommande.objects.create(
                commande=cmd, produit=produit, quantite=qte, 
                prix_unitaire=pu, sous_total=st
            )

            # Déduction stock boutique
            stock = StockParLocalisation.objects.get(produit=produit, localisation=loc_boutique)
            stock.quantite -= qte
            stock.save()
            
            # Historique mouvement
            MouvementStock.objects.create(
                produit=produit, localisation=loc_boutique, type='SORTIE',
                quantite=qte, reference_doc=cmd.numero, utilisateur=request.user
            )

        cmd.total_ht  = total_ht
        cmd.total_ttc = total_ht # Pas de TVA gérée ici pour simplifier
        cmd.save()

        # 3. Enregistrer le paiement
        if montant_paye > 0:
            Paiement.objects.create(
                commande=cmd, montant=montant_paye, 
                mode_paiement=mode_paiement, enregistre_par=request.user
            )
            if montant_paye >= cmd.total_ttc:
                cmd.statut_paiement = 'PAYE'
                cmd.statut = 'LIVREE' # Livraison immédiate
            else:
                cmd.statut_paiement = 'PARTIEL'
            cmd.save()

        messages.success(request, f"Vente {cmd.numero} enregistrée avec succès.")
        return redirect('web:commande_detail', pk=cmd.pk)

    except Exception as e:
        messages.error(request, f"Erreur lors de la vente : {e}")
        return redirect('web:vente_directe')


@login_required_web
def produit_search_htmx(request):
    """Recherche AJAX pour le panier de vente directe."""
    q = request.GET.get('q', '').strip()
    if not q: return render(request, 'web/commandes/_produit_results.html', {'produits': []})
    
    produits = Produit.objects.filter(actif=True).filter(
        nom__icontains=q
    ) | Produit.objects.filter(reference__icontains=q)
    
    return render(request, 'web/commandes/_produit_results.html', {
        'produits': produits.distinct()[:10]
    })


@employe_or_admin
def commande_action(request, pk, action):
    """Workflow de la commande (Valider, Expédier, etc.)."""
    cmd = get_object_or_404(Commande, pk=pk)
    
    if action == 'valider': cmd.statut = 'VALIDEE'
    elif action == 'preparer': cmd.statut = 'EN_PREPARATION'
    elif action == 'expedier': cmd.statut = 'EXPEDIEE'
    elif action == 'livrer':   cmd.statut = 'LIVREE'
    elif action == 'annuler':  cmd.statut = 'ANNULEE'
    
    cmd.save()
    messages.success(request, f"Commande {cmd.numero} mise à jour : {cmd.get_statut_display()}.")
    return redirect('web:commande_detail', pk=pk)


@employe_or_admin
def commande_paiement(request, pk):
    """Ajouter un paiement à une commande existante."""
    cmd = get_object_or_404(Commande, pk=pk)
    if request.method == 'POST':
        montant = float(request.POST.get('montant', 0))
        mode    = request.POST.get('mode_paiement', 'CASH')
        
        if montant > 0:
            Paiement.objects.create(
                commande=cmd, montant=montant, 
                mode_paiement=mode, enregistre_par=request.user
            )
            # Mise à jour statut paiement
            total_paye = sum(p.montant for p in cmd.paiements.all())
            if total_paye >= cmd.total_ttc:
                cmd.statut_paiement = 'PAYE'
            else:
                cmd.statut_paiement = 'PARTIEL'
            cmd.save()
            messages.success(request, "Paiement enregistré.")
            
    return redirect('web:commande_detail', pk=pk)
