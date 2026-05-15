"""
web/context_processors.py
Variables injectées dans TOUS les templates automatiquement :
  - user_role    : 'ADMIN' | 'EMPLOYE' | 'MAGASINIER'
  - alertes_stock : nombre de produits sous le seuil d'alerte
  - nb_commandes_attente : commandes en attente de validation
"""


def bsg_context(request):
    if not request.user.is_authenticated:
        return {}

    ctx = {
        'user_role':   request.user.role,
        'user_nom':    request.user.nom,
        'is_admin':    request.user.role == 'ADMIN',
        'is_employe':  request.user.role == 'EMPLOYE',
        'is_magasinier': request.user.role == 'MAGASINIER',
        'alertes_stock': 0,
        'nb_commandes_attente': 0,
    }

    try:
        from produits.models import Produit
        from django.db.models import F
        ctx['alertes_stock'] = Produit.objects.filter(
            quantite__lte=F('seuil_alerte'), actif=True
        ).count()
    except Exception:
        pass

    try:
        from commandes.models import Commande
        ctx['nb_commandes_attente'] = Commande.objects.filter(
            statut='EN_ATTENTE'
        ).count()
    except Exception:
        pass

    return ctx
