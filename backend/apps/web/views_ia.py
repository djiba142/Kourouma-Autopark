"""
web/views_ia.py
═════════════════════════════════════════════════════════════════════
Dashboard IA — 4 modules intégrés

  Toutes les vues sont Admin uniquement (données sensibles).
  Les modèles ML sont instanciés à la demande (lazy loading).
  Chaque vue entraîne le modèle sur les données récentes
  et retourne les résultats au template.
═════════════════════════════════════════════════════════════════════
"""
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from web.middleware import admin_required

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD IA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def dashboard_ia(request):
    """Page d'accueil du module IA — chiffres clés de chaque modèle."""
    from ia.models_ml import (
        PredicteurVentes, DetecteurAnomalies,
        RecommandeurProduits, AnalyseurRentabilite
    )

    ctx = {
        'title':   'Intelligence Artificielle BSG',
        'modules': [
            {
                'nom':         'Prédiction des Ventes',
                'icon':        'bi-graph-up-arrow',
                'color':       '#185FA5',
                'bg':          '#E6F1FB',
                'url':         'web:ia_ventes',
                'description': 'Prévision J+7 par produit. Alerte si stock insuffisant.',
            },
            {
                'nom':         'Détection d\'Anomalies',
                'icon':        'bi-shield-exclamation',
                'color':       '#C0392B',
                'bg':          '#FCE8E8',
                'url':         'web:ia_anomalies',
                'description': 'Opérations financières inhabituelles détectées par IA.',
            },
            {
                'nom':         'Recommandations Produits',
                'icon':        'bi-stars',
                'color':       '#BA7517',
                'bg':          '#FAEEDA',
                'url':         'web:ia_recommandations',
                'description': 'Ce que vos clients sont susceptibles d\'acheter ensuite.',
            },
            {
                'nom':         'Analyse Rentabilité (BCG)',
                'icon':        'bi-pie-chart',
                'color':       '#0F6E56',
                'bg':          '#E1F5EE',
                'url':         'web:ia_rentabilite',
                'description': 'Classement STAR / VACHE / DILEMME / POIDS_MORT.',
            },
        ]
    }

    # Compteurs rapides pour l'aperçu
    try:
        pred    = PredicteurVentes()
        alertes = [r for r in pred.predire(7) if r['alerte']]
        ctx['nb_alertes_stock'] = len(alertes)
    except Exception as e:
        logger.warning("[IA] Aperçu ventes échoué : %s", e)
        ctx['nb_alertes_stock'] = 0

    try:
        det       = DetecteurAnomalies()
        anomalies = [r for r in det.analyser(30) if r['anomalie']]
        ctx['nb_anomalies'] = len(anomalies)
    except Exception as e:
        logger.warning("[IA] Aperçu anomalies échoué : %s", e)
        ctx['nb_anomalies'] = 0

    try:
        anal  = AnalyseurRentabilite()
        bcg   = anal.analyser()
        ctx['nb_poids_morts'] = sum(1 for r in bcg if r['categorie'] == 'POIDS_MORT')
        ctx['nb_stars']       = sum(1 for r in bcg if r['categorie'] == 'STAR')
    except Exception as e:
        logger.warning("[IA] Aperçu BCG échoué : %s", e)
        ctx['nb_poids_morts'] = 0
        ctx['nb_stars']       = 0

    return render(request, 'web/ia/dashboard.html', ctx)


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 1 — PRÉDICTION DES VENTES
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def ia_ventes(request):
    from ia.models_ml import PredicteurVentes

    nb_jours = int(request.GET.get('jours', 7))
    nb_jours = max(1, min(nb_jours, 30))  # entre 1 et 30

    resultats = []
    erreur    = None

    try:
        pred = PredicteurVentes()
        pred.entrainer()
        resultats = pred.predire(nb_jours)
    except Exception as e:
        erreur = str(e)
        logger.error("[IA] Prédiction ventes : %s", e)

    alertes    = [r for r in resultats if r['alerte']]
    en_hausse  = [r for r in resultats if r['tendance'] == 'hausse']
    en_baisse  = [r for r in resultats if r['tendance'] == 'baisse']

    # Données graphique : total prévu par jour
    totaux_par_jour = [0.0] * nb_jours
    for r in resultats:
        for i, v in enumerate(r['vente_par_jour']):
            if i < nb_jours:
                totaux_par_jour[i] += v

    from datetime import date, timedelta
    labels_jours = [
        (date.today() + timedelta(days=i+1)).strftime('%d %b')
        for i in range(nb_jours)
    ]

    import json
    labels_jours_json = json.dumps(labels_jours)
    totaux_par_jour_json = json.dumps(totaux_par_jour)

    return render(request, 'web/ia/ventes.html', {
        'title':               'Prédiction des Ventes',
        'resultats':           resultats,
        'alertes':             alertes,
        'en_hausse':           en_hausse,
        'en_baisse':           en_baisse,
        'nb_jours':            nb_jours,
        'options_jours':       [7, 14, 21, 30],
        'labels_jours_json':   labels_jours_json,
        'totaux_par_jour_json': totaux_par_jour_json,
        'erreur':              erreur,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 2 — DÉTECTION D'ANOMALIES
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def ia_anomalies(request):
    from ia.models_ml import DetecteurAnomalies

    nb_jours = int(request.GET.get('jours', 30))
    resultats = []
    erreur    = None

    try:
        det       = DetecteurAnomalies()
        resultats = det.analyser(nb_jours)
    except Exception as e:
        erreur = str(e)
        logger.error("[IA] Détection anomalies : %s", e)

    critiques = [r for r in resultats if r['niveau'] == 'CRITIQUE']
    suspects  = [r for r in resultats if r['niveau'] == 'SUSPECT']
    normaux   = [r for r in resultats if r['niveau'] == 'NORMAL']

    return render(request, 'web/ia/anomalies.html', {
        'title':         'Détection d\'Anomalies',
        'resultats':     resultats,
        'critiques':     critiques,
        'suspects':      suspects,
        'normaux':       normaux,
        'nb_jours':      nb_jours,
        'options_jours': [7, 14, 30, 60],
        'erreur':        erreur,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 3 — RECOMMANDATIONS PRODUITS
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def ia_recommandations(request):
    from ia.models_ml import RecommandeurProduits
    from clients.models import Client

    client_id = request.GET.get('client_id')
    client    = None
    recos     = []
    erreur    = None

    try:
        reco = RecommandeurProduits()
        reco.entrainer()

        if client_id:
            client = Client.objects.filter(pk=client_id, actif=True).first()
            if client:
                recos = reco.recommander(client.id)
        else:
            # Sans client : top produits globaux
            recos = reco._top_produits_global(10)

    except Exception as e:
        erreur = str(e)
        logger.error("[IA] Recommandations : %s", e)

    return render(request, 'web/ia/recommandations.html', {
        'title':     'Recommandations Produits',
        'recos':     recos,
        'client':    client,
        'clients':   Client.objects.filter(actif=True).order_by('nom'),
        'client_id': client_id,
        'erreur':    erreur,
    })


# ─────────────────────────────────────────────────────────────────────────────
# MODULE 4 — ANALYSE RENTABILITÉ BCG
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
def ia_rentabilite(request):
    from ia.models_ml import AnalyseurRentabilite

    resultats = []
    erreur    = None

    try:
        anal      = AnalyseurRentabilite()
        resultats = anal.analyser()
    except Exception as e:
        erreur = str(e)
        logger.error("[IA] Rentabilité BCG : %s", e)

    stars       = [r for r in resultats if r['categorie'] == 'STAR']
    vaches      = [r for r in resultats if r['categorie'] == 'VACHE']
    dilemmes    = [r for r in resultats if r['categorie'] == 'DILEMME']
    poids_morts = [r for r in resultats if r['categorie'] == 'POIDS_MORT']

    from django.template.defaultfilters import slugify
    for r in resultats:
        r['cat_slug'] = slugify(r['categorie'])
        if r['categorie'] == 'STAR': r['cat_class'] = 'bg-success'
        elif r['categorie'] == 'VACHE': r['cat_class'] = 'bg-primary'
        elif r['categorie'] == 'DILEMME': r['cat_class'] = 'bg-warning'
        else: r['cat_class'] = 'bg-danger'

    # Données scatter pour Chart.js (marge vs volume)
    scatter_data = [
        {
            'x':    r['taux_marge'],
            'y':    r['volume'],
            'nom':  r['nom'][:20],
            'cat':  r['categorie'],
        }
        for r in resultats
    ]

    import json
    scatter_data_json = json.dumps(scatter_data)

    return render(request, 'web/ia/rentabilite.html', {
        'title':       'Analyse Rentabilité BCG',
        'resultats':   resultats,
        'stars':       stars,
        'vaches':      vaches,
        'dilemmes':    dilemmes,
        'poids_morts': poids_morts,
        'scatter_data_json': scatter_data_json,
        'erreur':      erreur,
    })


# ─────────────────────────────────────────────────────────────────────────────
# API JSON — pour rafraîchissement HTMX
# ─────────────────────────────────────────────────────────────────────────────

@admin_required
@require_GET
def ia_alertes_json(request):
    """Retourne le nombre d'alertes pour la navbar."""
    from ia.models_ml import PredicteurVentes, DetecteurAnomalies
    try:
        pred     = PredicteurVentes()
        alertes  = sum(1 for r in pred.predire(7) if r['alerte'])
        det      = DetecteurAnomalies()
        anomalies= sum(1 for r in det.analyser(7) if r['anomalie'])
        return JsonResponse({'alertes_stock': alertes, 'anomalies': anomalies, 'ok': True})
    except Exception as e:
        return JsonResponse({'alertes_stock': 0, 'anomalies': 0, 'ok': False, 'error': str(e)})
