"""
web/views_password_reset.py
Flux complet reset mot de passe par email :
  1. /mot-de-passe-oublie/     → saisie email
  2. Email envoyé avec lien token
  3. /reset/<token>/            → saisie nouveau mot de passe
  4. Confirmation + redirection login
"""
import logging
import secrets
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)

# Stockage simple en mémoire (pour petite équipe)
# En production avec beaucoup d'utilisateurs : utiliser un modèle DB
_tokens = {}   # {token: {'user_id': x, 'expires': datetime}}

TOKEN_EXPIRY_MINUTES = 30


def _clean_expired():
    """Nettoie les tokens expirés."""
    now = timezone.now()
    expired = [t for t, d in _tokens.items() if d['expires'] < now]
    for t in expired:
        del _tokens[t]


# ── ÉTAPE 1 — Demande de reset ────────────────────────────────────────────────

def password_reset_request(request):
    if request.user.is_authenticated:
        return redirect('web:dashboard')

    if request.method == 'GET':
        return render(request, 'web/auth/password_reset.html', {
            'title': 'Mot de passe oublié'
        })

    email = request.POST.get('email', '').strip().lower()

    if not email:
        messages.error(request, 'Email obligatoire.')
        return render(request, 'web/auth/password_reset.html', {'title': 'Mot de passe oublié'})

    from auth_users.models import Utilisateur

    # Toujours afficher le même message (anti-énumération)
    success_msg = (
        f'Si un compte existe pour {email}, '
        f'un email de réinitialisation a été envoyé.'
    )

    try:
        user = Utilisateur.objects.get(email=email, actif=True)

        # Générer token sécurisé
        token   = secrets.token_urlsafe(32)
        expires = timezone.now() + timedelta(minutes=TOKEN_EXPIRY_MINUTES)
        _clean_expired()
        _tokens[token] = {'user_id': user.id, 'expires': expires}

        # URL de reset
        reset_url = request.build_absolute_uri(f'/reset-password/{token}/')

        # Envoi email
        try:
            send_mail(
                subject='[BSG] Réinitialisation de votre mot de passe',
                message=(
                    f'Bonjour {user.nom},\n\n'
                    f'Cliquez sur ce lien pour réinitialiser votre mot de passe BSG :\n\n'
                    f'{reset_url}\n\n'
                    f'Ce lien est valable {TOKEN_EXPIRY_MINUTES} minutes.\n\n'
                    f'Si vous n\'avez pas fait cette demande, ignorez cet email.\n\n'
                    f'L\'équipe BSG'
                ),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bsg.com'),
                recipient_list=[email],
                fail_silently=False,
            )
            logger.info("[RESET] Email envoyé à %s", email)
        except Exception as e:
            logger.error("[RESET] Erreur envoi email : %s", e)
            # En développement : afficher le lien directement
            if settings.DEBUG:
                messages.info(request, f'[DEV] Lien de reset : {reset_url}')

    except Utilisateur.DoesNotExist:
        pass  # Ne pas révéler si l'email existe

    messages.success(request, success_msg)
    return redirect('web:login')


# ── ÉTAPE 2 — Nouveau mot de passe ───────────────────────────────────────────

def password_reset_confirm(request, token):
    _clean_expired()

    # Vérifier token
    if token not in _tokens:
        messages.error(request, 'Lien invalide ou expiré. Recommencez.')
        return redirect('web:password_reset_request')

    token_data = _tokens[token]
    if timezone.now() > token_data['expires']:
        del _tokens[token]
        messages.error(request, 'Lien expiré (30 minutes). Recommencez.')
        return redirect('web:password_reset_request')

    if request.method == 'GET':
        return render(request, 'web/auth/password_reset_confirm.html', {
            'title': 'Nouveau mot de passe',
            'token': token,
        })

    password = request.POST.get('password', '')
    confirm  = request.POST.get('password_confirm', '')

    errors = []
    if len(password) < 8:
        errors.append('Mot de passe trop court (minimum 8 caractères).')
    if password != confirm:
        errors.append('Les mots de passe ne correspondent pas.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return render(request, 'web/auth/password_reset_confirm.html', {
            'title': 'Nouveau mot de passe', 'token': token,
        })

    from auth_users.models import Utilisateur
    try:
        user = Utilisateur.objects.get(pk=token_data['user_id'])
        user.set_password(password)
        user.tentatives_echouees = 0
        user.derniere_tentative  = None
        user.save(update_fields=['password', 'tentatives_echouees', 'derniere_tentative'])
        del _tokens[token]
        logger.info("[RESET] Mot de passe changé pour %s", user.email)
        messages.success(request, '✅ Mot de passe changé. Connectez-vous.')
    except Utilisateur.DoesNotExist:
        messages.error(request, 'Erreur inattendue. Recommencez.')

    return redirect('web:login')
