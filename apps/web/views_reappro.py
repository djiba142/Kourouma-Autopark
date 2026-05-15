"""
web/views_reappro.py
Réapprovisionnement automatique IA :
  - Analyse les prédictions de vente
  - Génère automatiquement des suggestions de commandes achat
  - L'admin valide ou ignore chaque suggestion
  - Une fois validée, crée une CommandeAchat BROUILLON
"""
import logging
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction

from web.middleware import admin_required

logger = logging.getLogger(__name__)


@admin_required
def reappro_view(request):
    """
    Analyse les 7 prochains jours et liste les produits
    dont le stock prévu est insuffisant.
    """
    from ia.models_ml import PredicteurVentes
    from produits.models import Produit
    from achats.models import Fournisseur

    suggestions = []
    erreur      = None

    try:
        pred = PredicteurVentes()
        pred.entrainer()
        previsions = pred.predire(nb_jours=7)

        # Filtrer uniquement les alertes
        alertes = [p for p in previsions if p['alerte']]

        for a in alertes:
            produit = Produit.objects.filter(id=a['produit_id']).first()
            if not produit:
                continue

            # Quantité suggérée = manque + 20% de marge
            qte_suggeree = max(1, int(a['manque'] * 1.2))

            # Fournisseur par défaut (premier disponible)
            fournisseur = Fournisseur.objects.filter(actif=True).first()

            suggestions.append({
                'produit_id':    produit.id,
                'produit_nom':   produit.nom,
                'reference':     produit.reference,
                'stock_actuel':  a['stock_actuel'],
                'vente_prevue':  a['vente_prevue'],
                'manque':        a['manque'],
                'qte_suggeree':  qte_suggeree,
                'prix_achat':    float(produit.prix_achat or 0),
                'fournisseur':   fournisseur,
                'tendance':      a['tendance'],
            })

    except Exception as e:
        erreur = str(e)
        logger.error("[REAPPRO] Erreur prédiction : %s", e)

    fournisseurs = []
    try:
        from achats.models import Fournisseur
        fournisseurs = list(Fournisseur.objects.filter(actif=True).order_by('nom'))
    except Exception:
        pass

    return render(request, 'web/ia/reappro.html', {
        'title':        'Réapprovisionnement Automatique',
        'suggestions':  suggestions,
        'fournisseurs': fournisseurs,
        'erreur':       erreur,
        'nb_alertes':   len(suggestions),
    })


@admin_required
@transaction.atomic
def reappro_valider(request):
    """
    Crée une CommandeAchat BROUILLON depuis les suggestions validées.
    Reçoit les produits cochés + quantités ajustées depuis le formulaire.
    """
    if request.method != 'POST':
        return redirect('web:reappro')

    from achats.models import CommandeAchat, LigneAchat, Fournisseur
    from produits.models import Produit

    produits_ids = request.POST.getlist('produit_id')
    quantites    = request.POST.getlist('quantite')
    fourn_id     = request.POST.get('fournisseur_id')

    if not produits_ids:
        messages.error(request, 'Aucun produit sélectionné.')
        return redirect('web:reappro')

    fournisseur = get_object_or_404(Fournisseur, pk=fourn_id) if fourn_id else \
                  Fournisseur.objects.filter(actif=True).first()

    if not fournisseur:
        messages.error(request, 'Aucun fournisseur disponible.')
        return redirect('web:reappro')

    # Générer référence PO
    from datetime import datetime
    ref = f"PO-IA-{datetime.now().strftime('%y%m%d%H%M%S')}"

    achat = CommandeAchat.objects.create(
        reference=ref,
        fournisseur=fournisseur,
        statut='BROUILLON',
        devise='GNF',
        taux_change=1,
        date_commande=date.today(),
        cree_par=request.user,
        notes=f'Généré automatiquement par l\'IA BSG — Prédiction J+7',
    )

    total = 0
    nb    = 0
    for pid, qte_str in zip(produits_ids, quantites):
        qte = int(qte_str or 0)
        if qte <= 0:
            continue
        produit = Produit.objects.filter(pk=pid).first()
        if not produit:
            continue

        prix = float(produit.prix_achat or 0)
        LigneAchat.objects.create(
            achat=achat,
            produit=produit,
            quantite_cartons=qte,
            prix_unitaire_devise=prix,
        )
        total += qte * prix
        nb    += 1

    if nb == 0:
        achat.delete()
        messages.error(request, 'Aucune ligne valide. Commande annulée.')
        return redirect('web:reappro')

    achat.total_devise = total
    achat.total_gnf    = total
    achat.save(update_fields=['total_devise', 'total_gnf'])

    logger.info("[REAPPRO] PO %s créé par IA — %d produits", ref, nb)
    messages.success(
        request,
        f'✅ Commande achat {ref} créée avec {nb} produit(s). '
        f'Vérifiez et envoyez au fournisseur.'
    )
    return redirect('web:achat_detail', pk=achat.pk)
