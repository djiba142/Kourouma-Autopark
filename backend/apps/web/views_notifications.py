"""
web/views_notifications.py
Notifications stock critique :
  - Signal Django déclenché quand stock passe sous seuil_alerte
  - Badge rouge temps réel dans la navbar (HTMX polling)
  - Centre de notifications in-app
  - Email optionnel aux admins
"""
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

from web.middleware import login_required_web, admin_required

logger = logging.getLogger(__name__)

# ── Stockage in-memory des notifications non lues ────────────────────────────
# En production avec multi-workers : utiliser la DB ou Redis
_notifications = []   # [{id, type, titre, message, date, lu}]
_id_counter    = 0


def _add_notification(type_notif, titre, message, niveau='INFO'):
    global _id_counter
    _id_counter += 1
    _notifications.append({
        'id':      _id_counter,
        'type':    type_notif,
        'titre':   titre,
        'message': message,
        'niveau':  niveau,   # INFO / ALERTE / CRITIQUE
        'date':    timezone.now(),
        'lu':      False,
    })
    # Garder les 50 dernières uniquement
    if len(_notifications) > 50:
        _notifications.pop(0)


# ── Signal stock ──────────────────────────────────────────────────────────────

@receiver(post_save, sender='stock.StockParLocalisation')
def verifier_stock_apres_save(sender, instance, **kwargs):
    """
    Vérifié après chaque mise à jour de stock.
    Si quantite < seuil_alerte → notification CRITIQUE.
    Si quantite == 0 → notification CRITIQUE (rupture).
    """
    produit = instance.produit
    qte     = instance.quantite
    seuil   = produit.seuil_alerte or 0

    if qte <= 0:
        _add_notification(
            type_notif='STOCK_RUPTURE',
            titre=f'Rupture : {produit.nom}',
            message=f'Stock épuisé à {instance.localisation.nom}. Réapprovisionnement urgent.',
            niveau='CRITIQUE',
        )
        logger.warning("[STOCK] Rupture : %s @ %s", produit.nom, instance.localisation.nom)

        # Email optionnel
        _envoyer_email_stock(produit, instance.localisation, qte, seuil)

    elif seuil > 0 and qte <= seuil:
        _add_notification(
            type_notif='STOCK_ALERTE',
            titre=f'Stock faible : {produit.nom}',
            message=f'{qte} unités restantes @ {instance.localisation.nom} (seuil: {seuil}).',
            niveau='ALERTE',
        )
        logger.info("[STOCK] Alerte : %s — %d/%d @ %s",
                    produit.nom, qte, seuil, instance.localisation.nom)


def _envoyer_email_stock(produit, localisation, qte, seuil):
    """Envoie un email d'alerte aux admins (silencieux si non configuré)."""
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        from auth_users.models import Utilisateur

        admins = list(Utilisateur.objects.filter(
            role='ADMIN', actif=True
        ).values_list('email', flat=True))

        if not admins:
            return

        sujet = f'[BSG] ⚠ Stock {"épuisé" if qte == 0 else "faible"} : {produit.nom}'
        corps = (
            f'Bonjour,\n\n'
            f'Alerte stock BSG Dashboard :\n\n'
            f'Produit    : {produit.nom} ({produit.reference})\n'
            f'Stock      : {qte} unité(s)\n'
            f'Seuil      : {seuil} unité(s)\n'
            f'Site       : {localisation.nom}\n\n'
            f'Action recommandée : créer une commande achat fournisseur.\n\n'
            f'— BSG Dashboard'
        )
        send_mail(sujet, corps,
                  getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bsg.com'),
                  admins, fail_silently=True)
    except Exception as e:
        logger.debug("[NOTIF] Email stock non envoyé : %s", e)


# ── Vues ──────────────────────────────────────────────────────────────────────

@login_required_web
def notifications_json(request):
    """API JSON pour le badge navbar (HTMX polling toutes les 30s)."""
    non_lues = [n for n in _notifications if not n['lu']]
    critiques = [n for n in non_lues if n['niveau'] == 'CRITIQUE']
    return JsonResponse({
        'total':     len(non_lues),
        'critiques': len(critiques),
        'badge':     len(non_lues) if non_lues else 0,
    })


@login_required_web
def notifications_liste(request):
    """Centre de notifications."""
    # Regrouper par niveau pour l'affichage
    critiques = [n for n in reversed(_notifications) if n['niveau'] == 'CRITIQUE']
    alertes   = [n for n in reversed(_notifications) if n['niveau'] == 'ALERTE']
    infos     = [n for n in reversed(_notifications) if n['niveau'] == 'INFO']

    return render(request, 'web/notifications/liste.html', {
        'title':     'Notifications',
        'critiques': critiques[:10],
        'alertes':   alertes[:10],
        'infos':     infos[:10],
        'total_non_lu': sum(1 for n in _notifications if not n['lu']),
    })


@login_required_web
def notifications_marquer_lu(request):
    """Marque toutes les notifications comme lues."""
    for n in _notifications:
        n['lu'] = True
    return JsonResponse({'ok': True})


@login_required_web
def alertes_stock_vue(request):
    """Vue dédiée aux alertes stock actuelles (depuis la DB, pas les notifs)."""
    from produits.models import Produit
    from stock.models import StockParLocalisation

    ruptures = StockParLocalisation.objects.filter(
        quantite=0
    ).select_related('produit', 'localisation').order_by('produit__nom')

    alertes = StockParLocalisation.objects.filter(
        quantite__gt=0,
        produit__est_en_alerte=True
    ).select_related('produit', 'localisation').order_by('quantite')

    return render(request, 'web/notifications/alertes_stock.html', {
        'title':    'Alertes Stock',
        'ruptures': ruptures,
        'alertes':  alertes,
    })
