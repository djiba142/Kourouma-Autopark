"""
apps/ia/score_risque.py
Score de risque client 0→100 avec RandomForest.

Features utilisées :
  - ratio_dette_limite    : dette / limite_credit (0→∞)
  - pct_paiement          : total_paye / total_achats (0→1)
  - nb_commandes_impayes  : nombre de commandes non soldées
  - anciennete_jours      : jours depuis premier achat
  - frequence_achat       : commandes / ancienneté (cadence)

Score :
  0–30  → 🔴 RISQUE ÉLEVÉ  (bloquer le crédit)
  31–60 → 🟠 RISQUE MOYEN  (surveillance)
  61–85 → 🟡 BON CLIENT    (crédit normal)
  86–100 → 🟢 EXCELLENT     (augmenter limite)
"""
import logging
import numpy as np
from datetime import date

logger = logging.getLogger(__name__)


class ScoreRisqueClient:
    """Calcule le score de risque for all active clients."""

    def __init__(self):
        self.modele   = None
        self.entraine = False

    def _features_client(self, client):
        """Extrait les features d'un client."""
        from commandes.models import Commande

        limite = float(client.limite_credit) or 1
        dette  = float(client.total_dette)
        paye   = float(client.total_paye)
        achats = float(client.total_achats) or 1

        # Commandes impayées
        nb_impayes = Commande.objects.filter(
            client=client,
            statut_paiement__in=['NON_PAYE', 'PARTIEL'],
            statut__in=['VALIDEE', 'LIVREE'],
        ).count()

        # Ancienneté
        premiere = Commande.objects.filter(
            client=client
        ).order_by('date_creation').first()

        if premiere:
            anciennete = (date.today() - premiere.date_creation.date()).days
        else:
            anciennete = 0

        # Nombre total commandes
        nb_total = Commande.objects.filter(client=client).count()
        frequence = nb_total / max(anciennete, 1) * 30  # commandes/mois

        return [
            min(dette / limite, 5.0),          # ratio dette/limite (cappé à 5x)
            min(paye / achats, 1.0),            # taux paiement
            min(nb_impayes / max(nb_total, 1), 1.0),  # ratio impayés
            min(anciennete / 365, 5.0),         # ancienneté en années (cappé 5)
            min(frequence, 10.0),               # fréquence d'achat
        ]

    def calculer_score(self, client) -> dict:
        """
        Retourne le score de risque pour un client.
        Si pas assez de données pour le ML → règles heuristiques.
        """
        try:
            feats = self._features_client(client)
        except Exception as e:
            logger.warning("[SCORE] Features client %s : %s", client.id, e)
            return self._score_heuristique(client)

        # Score heuristique direct (plus fiable que ML avec peu de données)
        return self._score_heuristique_avec_features(client, feats)

    def _score_heuristique_avec_features(self, client, feats) -> dict:
        ratio_dette, taux_paye, ratio_impayes, anciennete, frequence = feats

        # Score de base 100
        score = 100

        # Pénalités
        score -= ratio_dette * 30           # -30 max si dette = limite
        score -= ratio_impayes * 25         # -25 max si tout impayé
        score -= (1 - taux_paye) * 20       # -20 max si rien payé
        if ratio_dette > 1:
            score -= 15                     # -15 supplémentaire si dépasse limite

        # Bonus
        score += min(anciennete, 3) * 3     # +9 max pour l'ancienneté
        score += min(frequence, 5) * 1      # +5 max pour la fréquence

        score = max(0, min(100, round(score)))

        if score >= 86:
            niveau, couleur, conseil = 'EXCELLENT',    '#1e8449', 'Augmenter la limite de crédit'
        elif score >= 61:
            niveau, couleur, conseil = 'BON',          '#185FA5', 'Crédit standard — surveiller régulièrement'
        elif score >= 31:
            niveau, couleur, conseil = 'MOYEN',        '#e67e22', 'Exiger paiement partiel avant livraison'
        else:
            niveau, couleur, conseil = 'RISQUE ÉLEVÉ', '#c0392b', 'Bloquer le crédit — recouvrement nécessaire'

        return {
            'client_id':  client.id,
            'nom':        client.nom,
            'telephone':  client.telephone,
            'score':      score,
            'niveau':     niveau,
            'couleur':    couleur,
            'conseil':    conseil,
            'dette':      float(client.total_dette),
            'limite':     float(client.limite_credit),
            'taux_paye':  round(float(feats[1]) * 100, 1),
        }

    def _score_heuristique(self, client) -> dict:
        """Fallback sans features calculées."""
        dette  = float(client.total_dette)
        limite = float(client.limite_credit) or 1
        ratio  = dette / limite

        if ratio == 0:      score = 85
        elif ratio < 0.5:   score = 70
        elif ratio < 1.0:   score = 50
        elif ratio < 1.5:   score = 25
        else:               score = 10

        if score >= 86:     niveau, couleur, conseil = 'EXCELLENT', '#1e8449', 'Augmenter la limite'
        elif score >= 61:   niveau, couleur, conseil = 'BON', '#185FA5', 'Crédit standard'
        elif score >= 31:   niveau, couleur, conseil = 'MOYEN', '#e67e22', 'Surveiller'
        else:               niveau, couleur, conseil = 'RISQUE ÉLEVÉ', '#c0392b', 'Bloquer le crédit'

        return {
            'client_id': client.id, 'nom': client.nom,
            'telephone': client.telephone,
            'score': score, 'niveau': niveau,
            'couleur': couleur, 'conseil': conseil,
            'dette': dette, 'limite': float(client.limite_credit),
            'taux_paye': 0,
        }

    def analyser_tous(self):
        """Retourne les scores de tous les clients actifs, triés par score croissant."""
        from clients.models import Client
        clients   = Client.objects.filter(actif=True)
        resultats = [self.calculer_score(c) for c in clients]
        resultats.sort(key=lambda r: r['score'])
        return resultats
