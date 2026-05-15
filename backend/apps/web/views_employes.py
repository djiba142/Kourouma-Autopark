"""
web/views_employes.py
═════════════════════════════════════════════════════════════════════
Gestion complète des employés (Admin uniquement) :

  1. Liste tous les utilisateurs avec statut + rôle
  2. Créer un nouvel employé  POST /employes/nouveau/
  3. Activer / Désactiver     POST /employes/<pk>/toggle/
  4. Changer le rôle          POST /employes/<pk>/role/
  5. Reset mot de passe       POST /employes/<pk>/reset-password/
     → L'admin choisit le nouveau mot de passe directement
       (pas d'email — adapté à une petite équipe sur place)
═════════════════════════════════════════════════════════════════════
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from web.middleware import admin_required
from auth_users.models import Utilisateur

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────
ROLES_VALIDES = dict(Utilisateur.ROLES)   # {'ADMIN': 'Administrateur', ...}
PASSWORD_MIN  = 8


# ─────────────────────────────────────────────────────────────────────────────
# 1 — LISTE DES EMPLOYÉS
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def employes_liste(request):
    users = Utilisateur.objects.order_by('role', 'nom')

    # Statistiques rapides pour l'en-tête
    stats = {
        'total':      users.count(),
        'actifs':     users.filter(actif=True).count(),
        'inactifs':   users.filter(actif=False).count(),
        'admins':     users.filter(role='ADMIN').count(),
        'employes':   users.filter(role='EMPLOYE').count(),
        'magasiniers':users.filter(role='MAGASINIER').count(),
    }

    return render(request, 'web/admin/employes_liste.html', {
        'title':  'Gestion des Employés',
        'users':  users,
        'stats':  stats,
        'roles':  Utilisateur.ROLES,
    })


@admin_required
def employes_export_pdf(request):
    """Génère un PDF de la liste des employés"""
    users = Utilisateur.objects.order_by('role', 'nom')
    html  = render_to_string('web/admin/employes_pdf.html', {
        'users': users,
        'date':  timezone.now(),
    }, request=request)

    try:
        from weasyprint import HTML
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="Liste_Employes.pdf"'
        return response
    except ImportError:
        return HttpResponse(html)


# ─────────────────────────────────────────────────────────────────────────────
# 2 — CRÉER UN EMPLOYÉ
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def employe_nouveau(request):
    if request.method == 'GET':
        return render(request, 'web/admin/employe_form.html', {
            'title': 'Créer un accès employé',
            'roles': Utilisateur.ROLES,
            'action': 'create',
        })

    # ── Récupération des champs ───────────────────────────────────────────────
    nom       = request.POST.get('nom', '').strip()
    email     = request.POST.get('email', '').strip().lower()
    telephone = request.POST.get('telephone', '').strip()
    password  = request.POST.get('password', '')
    confirm   = request.POST.get('password_confirm', '')
    role      = request.POST.get('role', 'EMPLOYE')

    # ── Validation ────────────────────────────────────────────────────────────
    errors = []
    if not nom:
        errors.append('Le nom complet est obligatoire.')
    if not email or '@' not in email:
        errors.append('Adresse email invalide.')
    if len(password) < PASSWORD_MIN:
        errors.append(f'Mot de passe trop court (minimum {PASSWORD_MIN} caractères).')
    if password != confirm:
        errors.append('Les deux mots de passe ne correspondent pas.')
    if role not in ROLES_VALIDES:
        errors.append('Rôle invalide.')
    if Utilisateur.objects.filter(email=email).exists():
        errors.append(f'L\'email {email} est déjà utilisé par un autre compte.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return render(request, 'web/admin/employe_form.html', {
            'title': 'Créer un accès employé',
            'roles': Utilisateur.ROLES,
            'action': 'create',
            'form_data': {'nom': nom, 'email': email, 'telephone': telephone, 'role': role},
        })

    # ── Création ──────────────────────────────────────────────────────────────
    user = Utilisateur.objects.create_user(
        email=email,
        nom=nom,
        telephone=telephone,
        password=password,
        role=role,
    )
    user.is_staff    = (role == 'ADMIN')
    user.is_active   = True
    user.actif       = True
    user.save(update_fields=['is_staff', 'is_active', 'actif'])

    logger.info("[EMPLOYE] Créé par %s : %s (%s)", request.user.nom, nom, role)
    messages.success(request, f'✅ Compte créé pour {nom} ({ROLES_VALIDES[role]}).')
    return redirect('web:employes_liste')


# ─────────────────────────────────────────────────────────────────────────────
# 3 — ACTIVER / DÉSACTIVER
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def employe_toggle_actif(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk)

    # Sécurité : l'admin ne peut pas se désactiver lui-même
    if user == request.user:
        messages.error(request, 'Vous ne pouvez pas désactiver votre propre compte.')
        return redirect('web:employes_liste')

    user.actif     = not user.actif
    user.is_active = user.actif   # synchronise avec le système Django
    user.save(update_fields=['actif', 'is_active'])

    etat = 'activé ✅' if user.actif else 'désactivé 🔒'
    logger.info("[EMPLOYE] %s %s par %s", user.nom, etat, request.user.nom)
    messages.success(request, f'{user.nom} — compte {etat}.')
    return redirect('web:employes_liste')


# ─────────────────────────────────────────────────────────────────────────────
# 4 — CHANGER LE RÔLE
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def employe_change_role(request, pk):
    user     = get_object_or_404(Utilisateur, pk=pk)
    nouveau  = request.POST.get('role', '').strip()

    if user == request.user:
        messages.error(request, 'Vous ne pouvez pas modifier votre propre rôle.')
        return redirect('web:employes_liste')

    if nouveau not in ROLES_VALIDES:
        messages.error(request, f'Rôle invalide : {nouveau}')
        return redirect('web:employes_liste')

    ancien       = user.role
    user.role    = nouveau
    user.is_staff = (nouveau == 'ADMIN')
    user.save(update_fields=['role', 'is_staff'])

    logger.info(
        "[EMPLOYE] Rôle %s : %s → %s (par %s)",
        user.nom, ancien, nouveau, request.user.nom
    )
    messages.success(
        request,
        f'Rôle de {user.nom} changé : {ROLES_VALIDES[ancien]} → {ROLES_VALIDES[nouveau]}.'
    )
    return redirect('web:employes_liste')


# ─────────────────────────────────────────────────────────────────────────────
# 5 — RESET MOT DE PASSE (par l'admin, sans email)
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def employe_reset_password(request, pk):
    user = get_object_or_404(Utilisateur, pk=pk)

    if request.method == 'GET':
        return render(request, 'web/admin/employe_reset_password.html', {
            'title':    f'Reset mot de passe — {user.nom}',
            'employe':  user,
        })

    password = request.POST.get('password', '')
    confirm  = request.POST.get('password_confirm', '')

    errors = []
    if len(password) < PASSWORD_MIN:
        errors.append(f'Mot de passe trop court (minimum {PASSWORD_MIN} caractères).')
    if password != confirm:
        errors.append('Les deux mots de passe ne correspondent pas.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return render(request, 'web/admin/employe_reset_password.html', {
            'title':   f'Reset mot de passe — {user.nom}',
            'employe': user,
        })

    # Appliquer le nouveau mot de passe
    user.set_password(password)
    # Reset les tentatives échouées
    user.tentatives_echouees = 0
    user.derniere_tentative  = None
    user.save(update_fields=['password', 'tentatives_echouees', 'derniere_tentative'])

    logger.info(
        "[SECURITE] Mot de passe de %s réinitialisé par %s",
        user.nom, request.user.nom
    )
    messages.success(
        request,
        f'✅ Mot de passe de {user.nom} réinitialisé. '
        f'Communiquez-lui son nouveau mot de passe en main propre.'
    )
    return redirect('web:employes_liste')
