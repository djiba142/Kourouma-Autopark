"""
web/views_objectifs.py
Objectifs de vente mensuels :
  - Admin fixe l'objectif du mois
  - Barre de progression visible par tous
  - Calcul automatique depuis le JournalFinancier
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q

from web.middleware import login_required_web, admin_required
from web.models import SettingDynamique


def _get_ventes_mois():
    """Retourne le total des encaissements du mois courant."""
    from finances.models import JournalFinancier
    now = timezone.now()
    return float(JournalFinancier.objects.filter(
        type_flux='ENTREE',
        type_operation__in=['VENTE', 'PAIEMENT'],
        created_at__year=now.year,
        created_at__month=now.month,
    ).aggregate(t=Sum('montant_gnf'))['t'] or 0)


def _get_objectif():
    """Lit l'objectif depuis les settings dynamiques (clé-valeur simple)."""
    try:
        val = SettingDynamique.objects.filter(cle='objectif_ventes_mensuel').first()
        return float(val.valeur) if val else 0
    except Exception:
        return 0


@login_required_web
def objectifs_view(request):
    ventes    = _get_ventes_mois()
    objectif  = _get_objectif()
    pct       = min(int(ventes / objectif * 100), 100) if objectif > 0 else 0
    manque    = max(0, objectif - ventes)
    depasse   = ventes > objectif and objectif > 0

    # Historique 6 derniers mois
    historique = []
    now = timezone.now()
    from finances.models import JournalFinancier
    for i in range(5, -1, -1):
        mois_dt  = (now.replace(day=1) - timezone.timedelta(days=i * 30)).replace(day=1)
        total    = float(JournalFinancier.objects.filter(
            type_flux='ENTREE',
            type_operation__in=['VENTE', 'PAIEMENT'],
            created_at__year=mois_dt.year,
            created_at__month=mois_dt.month,
        ).aggregate(t=Sum('montant_gnf'))['t'] or 0)
        historique.append({
            'label': mois_dt.strftime('%b %Y'),
            'total': total,
        })

    import json
    hist_labels = json.dumps([h['label'] for h in historique])
    hist_values = json.dumps([h['total'] for h in historique])

    return render(request, 'web/objectifs/objectifs.html', {
        'title':      'Objectifs de Vente',
        'ventes':     ventes,
        'objectif':   objectif,
        'pct':        pct,
        'manque':     manque,
        'depasse':    depasse,
        'hist_labels_json': hist_labels,
        'hist_values_json': hist_values,
        'is_admin':   request.user.role == 'ADMIN',
        'mois':       now.strftime('%B %Y'),
    })


@admin_required
def objectif_update(request):
    if request.method != 'POST':
        return redirect('web:objectifs')

    val = request.POST.get('objectif', '0').strip()
    try:
        montant = float(val)
        if montant < 0:
            raise ValueError

        try:
            obj, _ = SettingDynamique.objects.get_or_create(cle='objectif_ventes_mensuel')
            obj.valeur = str(montant)
            obj.save()
        except Exception:
            # Fallback : stocker dans la session
            request.session['objectif_ventes'] = montant

        messages.success(request, f'Objectif mis à jour : {montant:,.0f} GNF')
    except ValueError:
        messages.error(request, 'Montant invalide.')

    return redirect('web:objectifs')
