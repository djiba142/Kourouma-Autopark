"""
web/views_securite.py
Sécurité avancée :
  - Logs de connexion (IP, device, heure, succès/échec)
  - Vue admin des dernières connexions
  - Signal post-login pour enregistrer chaque tentative
"""
import logging
from django.shortcuts import render
from django.contrib.auth.signals import (
    user_logged_in, user_logged_out, user_login_failed
)
from django.dispatch import receiver
from django.utils import timezone
from web.models import LoginLog
from web.middleware import admin_required

logger = logging.getLogger(__name__)


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR', '')


# ── Signals Django Auth ───────────────────────────────────────────────────────

@receiver(user_logged_in)
def log_connexion_reussie(sender, request, user, **kwargs):
    try:
        LoginLog.objects.create(
            utilisateur=user,
            email_tente=user.email,
            succes=True,
            ip=_get_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        )
        logger.info("[AUTH] ✓ Connexion %s depuis %s", user.email, _get_ip(request))
    except Exception as e:
        logger.warning("[AUTH] Log connexion échoué : %s", e)


@receiver(user_login_failed)
def log_connexion_echouee(sender, credentials, request, **kwargs):
    try:
        email = credentials.get('username', credentials.get('email', ''))
        from auth_users.models import Utilisateur
        user = Utilisateur.objects.filter(email=email).first()

        LoginLog.objects.create(
            utilisateur=user,
            email_tente=email[:254],
            succes=False,
            ip=_get_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:300],
        )
        logger.warning("[AUTH] ✗ Tentative échouée : %s depuis %s", email, _get_ip(request))

        # Incrémenter tentatives échouées si utilisateur connu
        if user:
            user.tentatives_echouees = (user.tentatives_echouees or 0) + 1
            user.derniere_tentative  = timezone.now()

            # Bloquer après 10 tentatives
            if user.tentatives_echouees >= 10:
                user.actif     = False
                user.is_active = False
                logger.warning("[SECURITE] Compte %s bloqué après %d tentatives",
                               user.email, user.tentatives_echouees)

            user.save(update_fields=['tentatives_echouees', 'derniere_tentative', 'actif', 'is_active'])

    except Exception as e:
        logger.warning("[AUTH] Log tentative échouée : %s", e)


@receiver(user_logged_out)
def log_deconnexion(sender, request, user, **kwargs):
    if user:
        logger.info("[AUTH] Déconnexion %s", user.email)


# ── Vue admin logs ────────────────────────────────────────────────────────────

@admin_required
def logs_connexion(request):
    try:
        logs = LoginLog.objects.select_related('utilisateur').order_by('-date')[:200]
    except Exception:
        logs = []

    nb_echecs   = sum(1 for l in logs if not l.succes)
    nb_succes   = sum(1 for l in logs if l.succes)
    ips_suspectes = {}
    for l in logs:
        if not l.succes and l.ip:
            ips_suspectes[l.ip] = ips_suspectes.get(l.ip, 0) + 1
    ips_suspectes = sorted(ips_suspectes.items(), key=lambda x: -x[1])[:5]

    return render(request, 'web/admin/logs_connexion.html', {
        'title':          'Logs de Connexion',
        'logs':           logs,
        'nb_echecs':      nb_echecs,
        'nb_succes':      nb_succes,
        'ips_suspectes':  ips_suspectes,
    })
