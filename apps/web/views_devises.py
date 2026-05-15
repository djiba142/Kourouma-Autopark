"""
web/views_devises.py
Taux de change multi-devises (GNF/USD/EUR/CNY)
Source : exchangerate-api.com (gratuit 1500 req/mois)
Cache : 6 heures en mémoire (pas de dépendance Redis)
Admin peut forcer une mise à jour manuelle.
"""
import logging
import json
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from web.middleware import login_required_web, admin_required

logger = logging.getLogger(__name__)

# ── Cache en mémoire ──────────────────────────────────────────────────────────
_cache = {
    'taux':      {},
    'mis_a_jour': None,
}
CACHE_TTL_HEURES = 6

# Taux de repli si l'API est indisponible
TAUX_DEFAUT = {
    'USD': 8650.0,   # 1 USD = 8650 GNF (approximatif)
    'EUR': 9400.0,   # 1 EUR = 9400 GNF
    'CNY': 1200.0,   # 1 CNY = 1200 GNF
    'GBP': 11000.0,  # 1 GBP = 11000 GNF
    'XOF': 14.3,     # 1 XOF = 14.3 GNF (FCFA)
    'GNF': 1.0,
}

DEVISES_LABELS = {
    'USD': '🇺🇸 Dollar américain',
    'EUR': '🇪🇺 Euro',
    'CNY': '🇨🇳 Yuan chinois',
    'GBP': '🇬🇧 Livre sterling',
    'XOF': '🌍 Franc CFA (CEDEAO)',
    'GNF': '🇬🇳 Franc guinéen',
}


def _cache_valide():
    if not _cache['mis_a_jour'] or not _cache['taux']:
        return False
    age = datetime.now() - _cache['mis_a_jour']
    return age < timedelta(hours=CACHE_TTL_HEURES)


def _charger_taux_api():
    """Charge les taux depuis exchangerate-api.com (base GNF)."""
    import urllib.request
    try:
        # API gratuite sans clé pour les taux de base USD
        url = 'https://api.exchangerate-api.com/v4/latest/USD'
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
        rates_usd = data.get('rates', {})   # taux par rapport à 1 USD
        gnf_per_usd = rates_usd.get('GNF', 8650.0)

        taux = {}
        for code in TAUX_DEFAUT:
            if code == 'GNF':
                taux[code] = 1.0
            elif code in rates_usd:
                taux[code] = gnf_per_usd / rates_usd[code]
            else:
                taux[code] = TAUX_DEFAUT[code]

        _cache['taux']      = taux
        _cache['mis_a_jour'] = datetime.now()
        logger.info("[DEVISES] Taux mis à jour depuis l'API")
        return taux, True

    except Exception as e:
        logger.warning("[DEVISES] API indisponible (%s) — taux de repli utilisés", e)
        if not _cache['taux']:
            _cache['taux']      = TAUX_DEFAUT.copy()
            _cache['mis_a_jour'] = datetime.now()
        return _cache['taux'], False


def get_taux_gnf(devise: str) -> float:
    """Retourne combien de GNF vaut 1 unité de la devise donnée."""
    if not _cache_valide():
        _charger_taux_api()
    return _cache['taux'].get(devise.upper(), TAUX_DEFAUT.get(devise.upper(), 1.0))


def convertir(montant: float, devise_source: str, devise_cible: str = 'GNF') -> float:
    """Convertit un montant entre deux devises via GNF comme pivot."""
    taux_source = get_taux_gnf(devise_source)
    if devise_cible == 'GNF':
        return montant * taux_source
    taux_cible = get_taux_gnf(devise_cible)
    return montant * taux_source / taux_cible


# ── Vues Django ───────────────────────────────────────────────────────────────

@login_required_web
def devises_view(request):
    taux, depuis_api = _charger_taux_api() if not _cache_valide() else (_cache['taux'], True)

    # Calculer l'équivalent de 1 000 000 GNF dans chaque devise
    equivalences = {
        code: round(1_000_000 / taux[code], 2) if taux.get(code, 0) > 0 else 0
        for code in taux
    }

    return render(request, 'web/admin/devises.html', {
        'title':       'Taux de Change',
        'taux':        taux,
        'equivalences': equivalences,
        'labels':      DEVISES_LABELS,
        'mis_a_jour':  _cache['mis_a_jour'],
        'depuis_api':  depuis_api,
        'cache_valide': _cache_valide(),
    })


@admin_required
def devises_refresh(request):
    """Force le rechargement des taux depuis l'API."""
    _cache['mis_a_jour'] = None   # invalide le cache
    taux, ok = _charger_taux_api()
    if ok:
        messages.success(request, '✅ Taux de change mis à jour depuis l\'API.')
    else:
        messages.warning(request, '⚠ API indisponible — taux de repli utilisés.')
    return redirect('web:devises')


@login_required_web
def devises_convertir_json(request):
    """API JSON pour le convertisseur en temps réel (HTMX)."""
    try:
        montant = float(request.GET.get('montant', 0))
        source  = request.GET.get('de', 'USD').upper()
        cible   = request.GET.get('vers', 'GNF').upper()
        result  = convertir(montant, source, cible)
        return JsonResponse({
            'resultat': round(result, 2),
            'resultat_fmt': f"{result:,.2f} {cible}",
            'taux': get_taux_gnf(source),
        })
    except Exception as e:
        return JsonResponse({'erreur': str(e)}, status=400)
