"""
web/views_admin.py
Gestion des accès, journal d'audit et catalogue produits.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from web.middleware import admin_required, login_required_web
from auth_users.models import Utilisateur
from audit.models import AuditLog
from produits.models import Produit


@admin_required
def gestion_acces(request):
    return render(request, 'web/admin/utilisateurs.html', {
        'title': 'Gestion des accès',
        'users': Utilisateur.objects.all(),
        'roles': Utilisateur.ROLES
    })


@admin_required
def user_toggle_actif(request, pk):
    u = get_object_or_404(Utilisateur, pk=pk)
    u.actif = not u.actif
    u.save()
    messages.success(request, f"Statut de {u.nom} mis à jour.")
    return redirect('web:gestion_acces')


@admin_required
def user_change_role(request, pk):
    if request.method == 'POST':
        u = get_object_or_404(Utilisateur, pk=pk)
        u.role = request.POST.get('role')
        u.save()
        messages.success(request, f"Rôle de {u.nom} mis à jour.")
    return redirect('web:gestion_acces')


@admin_required
def audit_liste(request):
    return render(request, 'web/admin/audit.html', {
        'title': "Journal d'audit",
        'logs': AuditLog.objects.select_related('utilisateur').order_by('-date')[:200]
    })


@login_required_web
def produits_liste(request):
    return render(request, 'web/stock/produits.html', {
        'title': 'Catalogue Produits',
        'produits': Produit.objects.filter(actif=True).order_by('nom')
    })


@admin_required
def produit_nouveau(request):
    from produits.models import Categorie, Marque
    if request.method == 'POST':
        reference = request.POST.get('reference')
        nom = request.POST.get('nom')
        categorie_id = request.POST.get('categorie')
        prix_achat = request.POST.get('prix_achat', 0)
        prix_vente = request.POST.get('prix_vente', 0)
        seuil_alerte = request.POST.get('seuil_alerte', 5)

        if not reference or not nom:
            messages.error(request, "La référence et le nom sont obligatoires.")
        elif Produit.objects.filter(reference=reference).exists():
            messages.error(request, "Cette référence existe déjà.")
        else:
            Produit.objects.create(
                reference=reference,
                nom=nom,
                categorie_id=categorie_id if categorie_id else None,
                prix_achat=prix_achat,
                prix_vente=prix_vente,
                seuil_alerte=seuil_alerte,
            )
            messages.success(request, f"Produit {nom} ajouté au catalogue.")
            return redirect('web:produits_liste')

    return render(request, 'web/stock/produit_form.html', {
        'title': 'Nouveau Produit',
        'categories': Categorie.objects.all()
    })
