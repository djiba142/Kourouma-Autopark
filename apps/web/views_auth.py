"""
web/views_auth.py
Login / Logout / Création compte (Admin only)
Auth par sessions Django — pas de JWT.
"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from web.middleware import admin_required, login_required_web


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────────────────────────────────────

@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('web:dashboard')

    if request.method == 'GET':
        return render(request, 'web/auth/login.html')

    identifiant = request.POST.get('identifiant', '').strip()
    password    = request.POST.get('password', '')

    # Validation rapide
    if not identifiant or not password:
        messages.error(request, 'Identifiant et mot de passe obligatoires.')
        return render(request, 'web/auth/login.html', {'identifiant': identifiant})

    from auth_users.models import Utilisateur
    from django.db.models import Q
    try:
        user_obj = Utilisateur.objects.get(Q(email=identifiant) | Q(telephone=identifiant))
        if not user_obj.actif:
            messages.error(request, 'Compte désactivé. Contactez votre administrateur.')
            return render(request, 'web/auth/login.html', {'identifiant': identifiant})
    except Utilisateur.DoesNotExist:
        pass

    user = authenticate(request, username=identifiant, password=password)

    if user is None:
        # Incrémenter tentatives échouées
        try:
            from django.db.models import Q
            u = Utilisateur.objects.get(Q(email=identifiant) | Q(telephone=identifiant))
            u.tentatives_echouees += 1
            u.derniere_tentative = timezone.now()
            u.save(update_fields=['tentatives_echouees', 'derniere_tentative'])
        except Utilisateur.DoesNotExist:
            pass
        messages.error(request, 'Identifiants incorrects. Vérifiez votre email/téléphone et mot de passe.')
        return render(request, 'web/auth/login.html', {'identifiant': identifiant})

    # Succès — reset tentatives, ouvrir session
    user.tentatives_echouees = 0
    user.derniere_tentative  = None
    user.save(update_fields=['tentatives_echouees', 'derniere_tentative'])

    login(request, user)
    next_url = request.GET.get('next', '/dashboard/')
    return redirect(next_url)


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

@login_required_web
def logout_view(request):
    logout(request)
    messages.success(request, 'Déconnexion réussie.')
    return redirect('web:login')


# ─────────────────────────────────────────────────────────────────────────────
# CRÉATION UTILISATEUR (Admin only)
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
@require_http_methods(['GET', 'POST'])
def create_user_view(request):
    if request.method == 'GET':
        return render(request, 'web/auth/create_user.html')

    nom       = request.POST.get('nom', '').strip()
    email     = request.POST.get('email', '').strip()
    telephone = request.POST.get('telephone', '').strip() or None
    password  = request.POST.get('password', '')
    role      = request.POST.get('role', 'EMPLOYE')

    errors = []
    if not nom:      errors.append('Nom obligatoire.')
    if not email:    errors.append('Email obligatoire.')
    if len(password) < 8: errors.append('Mot de passe trop court (min. 8 caractères).')
    if role not in ('ADMIN', 'EMPLOYE', 'MAGASINIER'):
        errors.append('Rôle invalide.')

    if errors:
        for e in errors:
            messages.error(request, e)
        return render(request, 'web/auth/create_user.html',
                      {'nom': nom, 'email': email, 'role': role, 'telephone': telephone})

    from auth_users.models import Utilisateur
    if Utilisateur.objects.filter(email=email).exists():
        messages.error(request, 'Cet email est déjà utilisé.')
        return render(request, 'web/auth/create_user.html',
                      {'nom': nom, 'email': email, 'role': role, 'telephone': telephone})
    
    if telephone and Utilisateur.objects.filter(telephone=telephone).exists():
        messages.error(request, 'Ce numéro de téléphone est déjà utilisé.')
        return render(request, 'web/auth/create_user.html',
                      {'nom': nom, 'email': email, 'role': role, 'telephone': telephone})

    Utilisateur.objects.create_user(
        email=email, nom=nom, telephone=telephone, password=password, role=role
    )
    messages.success(request, f'Compte créé pour {nom} ({role}).')
    return redirect('web:gestion_acces')
