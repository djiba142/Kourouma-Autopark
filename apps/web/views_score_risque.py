"""web/views_score_risque.py — Score risque client IA"""
import logging
from django.shortcuts import render
from web.middleware import admin_required
logger = logging.getLogger(__name__)

@admin_required
def score_risque_view(request):
    from ia.score_risque import ScoreRisqueClient
    resultats = []
    erreur    = None
    try:
        scorer    = ScoreRisqueClient()
        resultats = scorer.analyser_tous()
    except Exception as e:
        erreur = str(e)
        logger.error("[SCORE RISQUE] %s", e)
    risque_eleve = [r for r in resultats if r['score'] < 31]
    risque_moyen = [r for r in resultats if 31 <= r['score'] < 61]
    bons         = [r for r in resultats if r['score'] >= 61]
    return render(request, 'web/ia/score_risque.html', {
        'title': 'Score Risque Clients', 'resultats': resultats,
        'risque_eleve': risque_eleve, 'risque_moyen': risque_moyen,
        'bons': bons, 'erreur': erreur,
    })
