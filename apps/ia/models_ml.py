"""
apps/ia/models_ml.py
═════════════════════════════════════════════════════════════════════
4 MODÈLES ML INTÉGRÉS À BSG — scikit-learn pur, zéro dépendance cloud

  1. PredicteurVentes
     → LinearRegression sur historique J-30 à J-1
     → Prédit les ventes des 7 prochains jours par produit
     → Déclenche une alerte "commander maintenant" si stock < prévision

  2. DetecteurAnomalies
     → IsolationForest sur les montants du JournalFinancier
     → Score d'anomalie -1 = suspect, 1 = normal
     → Remonte les 5 opérations les plus anormales

  3. RecommandeurProduits
     → NearestNeighbors sur matrice client × produit
     → "Les clients qui ont acheté X achètent aussi Y"
     → Top 5 recommandations par client

  4. AnalyseurRentabilite
     → Clustering KMeans sur (marge, volume, rotation)
     → Classe chaque produit : STAR / VACHE / POIDS_MORT / DILEMME
     → Matrice BCG simplifiée

UTILISATION :
  from ia.models_ml import PredicteurVentes, DetecteurAnomalies, ...
  pred = PredicteurVentes()
  pred.entrainer()
  resultats = pred.predire(nb_jours=7)
═════════════════════════════════════════════════════════════════════
"""
import logging
import numpy as np
from datetime import date, timedelta
from django.db.models import Sum, Count, Avg, F
from django.utils import timezone

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# 1 — PRÉDICTEUR DE VENTES
# ─────────────────────────────────────────────────────────────────────────────

class PredicteurVentes:
    """
    Prédit les ventes des N prochains jours par produit.
    Algorithme : régression linéaire sur fenêtre glissante 30 jours.
    Déclencheur : alerte si stock prévu insuffisant.
    """

    def __init__(self):
        self.modeles     = {}   # {produit_id: LinearRegression}
        self.historiques = {}   # {produit_id: [ventes_jour_1, ..., ventes_jour_30]}
        self.entraine    = False

    def _charger_historique(self, nb_jours: int = 60):
        """Charge les ventes quotidiennes par produit sur nb_jours."""
        from commandes.models import LigneCommande

        aujourd_hui = date.today()
        debut       = aujourd_hui - timedelta(days=nb_jours)

        lignes = LigneCommande.objects.filter(
            commande__date_creation__date__gte=debut,
            commande__statut__in=['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE'],
        ).values(
            'produit_id',
            'commande__date_creation__date',
        ).annotate(
            total_vendu=Sum('quantite')
        )

        data = {}
        for l in lignes:
            pid  = l['produit_id']
            jour = l['commande__date_creation__date']
            if pid not in data:
                data[pid] = {}
            data[pid][jour] = l['total_vendu']

        # Transformer en série temporelle continue (0 si pas de vente ce jour)
        self.historiques = {}
        for pid, ventes in data.items():
            serie = []
            for i in range(nb_jours):
                d = aujourd_hui - timedelta(days=nb_jours - i)
                serie.append(float(ventes.get(d, 0)))
            self.historiques[pid] = serie

        return self.historiques

    def entrainer(self, nb_jours: int = 60):
        """Entraîne un modèle de régression par produit."""
        try:
            from sklearn.linear_model import LinearRegression
        except ImportError:
            logger.error("scikit-learn non installé. Lancer: pip install scikit-learn")
            return False

        self._charger_historique(nb_jours)

        for pid, serie in self.historiques.items():
            if len(serie) < 7:
                continue
            # Features : indices temporels (0, 1, 2, ...)
            X = np.array(range(len(serie))).reshape(-1, 1)
            y = np.array(serie)
            m = LinearRegression()
            m.fit(X, y)
            self.modeles[pid] = {'model': m, 'len': len(serie)}

        self.entraine = True
        logger.info("[IA] PredicteurVentes entraîné sur %d produits", len(self.modeles))
        return True

    def predire(self, nb_jours: int = 7):
        """
        Retourne les prévisions de vente + alertes stock insuffisant.
        """
        if not self.entraine:
            self.entrainer()

        from produits.models import Produit

        resultats = []
        produits  = {p.id: p for p in Produit.objects.filter(actif=True)}

        for pid, info in self.modeles.items():
            if pid not in produits:
                continue

            produit = produits[pid]
            m       = info['model']
            base    = info['len']

            # Prédire les nb_jours prochains
            X_futur    = np.array(range(base, base + nb_jours)).reshape(-1, 1)
            predictions = np.maximum(m.predict(X_futur), 0)  # pas de négatifs

            total_prevu = float(predictions.sum())
            stock_actuel = float(produit.quantite)

            resultats.append({
                'produit_id':   pid,
                'produit_nom':  produit.nom,
                'reference':    produit.reference,
                'stock_actuel': stock_actuel,
                'vente_prevue': round(total_prevu, 1),
                'vente_par_jour': [round(float(v), 1) for v in predictions],
                'alerte':       stock_actuel < total_prevu,
                'manque':       max(0, round(total_prevu - stock_actuel, 1)),
                'tendance':     'hausse' if m.coef_[0] > 0.05 else
                               'baisse' if m.coef_[0] < -0.05 else 'stable',
            })

        # Trier : alertes d'abord, puis par vente prévue décroissante
        resultats.sort(key=lambda r: (-int(r['alerte']), -r['vente_prevue']))
        return resultats


# ─────────────────────────────────────────────────────────────────────────────
# 2 — DÉTECTEUR D'ANOMALIES
# ─────────────────────────────────────────────────────────────────────────────

class DetecteurAnomalies:
    """
    Détecte les opérations financières inhabituelles.
    Algorithme : IsolationForest sur [montant, heure, type_flux encodé].
    Score < -0.1 = suspecte.
    """

    def __init__(self):
        self.modele   = None
        self.entraine = False

    def entrainer(self, nb_jours: int = 90):
        """Entraîne l'IsolationForest sur l'historique journal."""
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
        except ImportError:
            logger.error("scikit-learn non installé.")
            return False

        from finances.models import JournalFinancier

        debut = timezone.now() - timedelta(days=nb_jours)
        ops   = JournalFinancier.objects.filter(created_at__gte=debut)

        if ops.count() < 10:
            logger.warning("[IA] Pas assez de données pour IsolationForest (%d ops)", ops.count())
            return False

        # Features : [montant_gnf, heure (0-23), flux (0=ENTREE, 1=SORTIE)]
        X = []
        for op in ops:
            X.append([
                float(op.montant_gnf),
                op.created_at.hour,
                0 if op.type_flux == 'ENTREE' else 1,
            ])

        X_arr = np.array(X)
        self.scaler = StandardScaler()
        X_scaled    = self.scaler.fit_transform(X_arr)

        self.modele = IsolationForest(
            contamination=0.05,   # 5% d'anomalies attendues
            random_state=42,
            n_estimators=100,
        )
        self.modele.fit(X_scaled)
        self.entraine = True
        logger.info("[IA] DetecteurAnomalies entraîné sur %d opérations", len(X))
        return True

    def analyser(self, nb_jours: int = 30):
        """
        Retourne les opérations suspectes des nb_jours derniers.
        """
        if not self.entraine:
            ok = self.entrainer()
            if not ok:
                return []

        from finances.models import JournalFinancier

        debut = timezone.now() - timedelta(days=nb_jours)
        ops   = list(JournalFinancier.objects.filter(
            created_at__gte=debut
        ).select_related('utilisateur').order_by('-created_at'))

        if not ops:
            return []

        X = np.array([
            [float(op.montant_gnf), op.created_at.hour,
             0 if op.type_flux == 'ENTREE' else 1]
            for op in ops
        ])
        X_scaled = self.scaler.transform(X)
        scores   = self.modele.score_samples(X_scaled)  # plus bas = plus anormal
        labels   = self.modele.predict(X_scaled)        # -1 = anomalie

        resultats = []
        for op, score, label in zip(ops, scores, labels):
            niveau = 'NORMAL'
            if label == -1:
                if score < -0.3:   niveau = 'CRITIQUE'
                elif score < -0.1: niveau = 'SUSPECT'

            resultats.append({
                'operation_id': op.id,
                'numero':       op.numero,
                'type':         op.type_operation,
                'flux':         op.type_flux,
                'montant':      float(op.montant_gnf),
                'heure':        op.created_at.strftime('%d/%m %H:%M'),
                'utilisateur':  op.utilisateur.nom if op.utilisateur else '—',
                'description':  op.description[:60],
                'score':        round(float(score), 3),
                'niveau':       niveau,
                'anomalie':     label == -1,
            })

        # Trier : anomalies d'abord
        resultats.sort(key=lambda r: r['score'])
        return resultats[:20]  # Top 20 plus suspects


# ─────────────────────────────────────────────────────────────────────────────
# 3 — RECOMMANDEUR DE PRODUITS
# ─────────────────────────────────────────────────────────────────────────────

class RecommandeurProduits:
    """
    Recommande des produits basé sur l'historique d'achats des clients.
    Algorithme : Collaborative Filtering avec NearestNeighbors.
    Fallback : top produits globaux si client inconnu.
    """

    def __init__(self):
        self.modele       = None
        self.matrice      = None
        self.produit_ids  = []
        self.client_ids   = []
        self.entraine     = False

    def entrainer(self):
        """Construit la matrice client × produit et entraîne KNN."""
        try:
            from sklearn.neighbors import NearestNeighbors
        except ImportError:
            logger.error("scikit-learn non installé.")
            return False

        from commandes.models import LigneCommande

        # Matrice d'achats client × produit (quantité totale)
        achats = LigneCommande.objects.filter(
            commande__client__isnull=False,
            commande__statut__in=['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE'],
        ).values(
            'commande__client_id', 'produit_id'
        ).annotate(qte_totale=Sum('quantite'))

        if achats.count() < 5:
            logger.warning("[IA] Pas assez de données pour les recommandations")
            return False

        # Construire la matrice creuse
        client_set  = sorted(set(a['commande__client_id'] for a in achats))
        produit_set = sorted(set(a['produit_id'] for a in achats))

        self.client_ids  = client_set
        self.produit_ids = produit_set

        c_idx = {c: i for i, c in enumerate(client_set)}
        p_idx = {p: i for i, p in enumerate(produit_set)}

        matrice = np.zeros((len(client_set), len(produit_set)))
        for a in achats:
            ci = c_idx[a['commande__client_id']]
            pi = p_idx[a['produit_id']]
            matrice[ci][pi] = float(a['qte_totale'])

        self.matrice = matrice
        self.modele  = NearestNeighbors(
            metric='cosine',
            algorithm='brute',
            n_neighbors=min(6, len(client_set)),
        )
        self.modele.fit(matrice)
        self.entraine = True
        logger.info(
            "[IA] RecommandeurProduits entraîné — %d clients, %d produits",
            len(client_set), len(produit_set)
        )
        return True

    def recommander(self, client_id: int, top_n: int = 5):
        """
        Retourne top_n produits recommandés pour le client.
        """
        if not self.entraine:
            ok = self.entrainer()
            if not ok:
                return self._top_produits_global(top_n)

        if client_id not in self.client_ids:
            return self._top_produits_global(top_n)

        from produits.models import Produit

        idx_client  = self.client_ids.index(client_id)
        vecteur     = self.matrice[idx_client].reshape(1, -1)

        # Trouver les clients similaires
        distances, indices = self.modele.kneighbors(vecteur)

        # Agréger les produits achetés par les voisins mais pas par le client
        scores = np.zeros(len(self.produit_ids))
        deja_achete = set(
            i for i, v in enumerate(self.matrice[idx_client]) if v > 0
        )

        for i, (dist, idx) in enumerate(zip(distances[0][1:], indices[0][1:])):
            poids = 1 - dist   # plus proche = poids plus fort
            scores += self.matrice[idx] * poids

        # Exclure ce que le client a déjà acheté
        for i in deja_achete:
            scores[i] = 0

        top_indices = np.argsort(scores)[::-1][:top_n]

        produit_ids_reco = [self.produit_ids[i] for i in top_indices if scores[i] > 0]
        produits         = {p.id: p for p in Produit.objects.filter(id__in=produit_ids_reco)}

        return [
            {
                'produit_id':  pid,
                'nom':         produits[pid].nom if pid in produits else '—',
                'reference':   produits[pid].reference if pid in produits else '—',
                'prix_vente':  float(produits[pid].prix_vente) if pid in produits else 0,
                'score':       round(float(scores[self.produit_ids.index(pid)]), 2),
                'stock_ok':    produits[pid].quantite > 0 if pid in produits else False,
            }
            for pid in produit_ids_reco
            if pid in produits
        ]

    def _top_produits_global(self, top_n: int = 5):
        """Fallback : top produits les plus vendus globalement."""
        from commandes.models import LigneCommande
        from produits.models import Produit

        tops = LigneCommande.objects.filter(
            commande__statut__in=['VALIDEE', 'LIVREE']
        ).values('produit_id').annotate(
            total=Sum('quantite')
        ).order_by('-total')[:top_n]

        produits = {p.id: p for p in Produit.objects.filter(
            id__in=[t['produit_id'] for t in tops]
        )}

        return [
            {
                'produit_id': t['produit_id'],
                'nom':        produits[t['produit_id']].nom if t['produit_id'] in produits else '—',
                'reference':  produits[t['produit_id']].reference if t['produit_id'] in produits else '—',
                'prix_vente': float(produits[t['produit_id']].prix_vente) if t['produit_id'] in produits else 0,
                'score':      float(t['total']),
                'stock_ok':   produits[t['produit_id']].quantite > 0 if t['produit_id'] in produits else False,
            }
            for t in tops if t['produit_id'] in produits
        ]


# ─────────────────────────────────────────────────────────────────────────────
# 4 — ANALYSEUR DE RENTABILITÉ (Matrice BCG)
# ─────────────────────────────────────────────────────────────────────────────

class AnalyseurRentabilite:
    """
    Classe les produits en 4 catégories BCG avec KMeans.
    Features : [taux_marge, volume_ventes, rotation_stock]
    Catégories :
      STAR       → marge haute + volume élevé
      VACHE      → marge haute + volume faible (fidèle mais limité)
      DILEMME    → marge faible + volume élevé (à optimiser)
      POIDS_MORT → marge faible + volume faible (à abandonner)
    """

    def __init__(self):
        self.modele   = None
        self.scaler   = None
        self.entraine = False

    def analyser(self):
        """
        Retourne la classification BCG de tous les produits actifs.
        Entraîne le modèle à la volée.
        """
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import MinMaxScaler
        except ImportError:
            logger.error("scikit-learn non installé.")
            return []

        from produits.models import Produit
        from commandes.models import LigneCommande

        produits = list(Produit.objects.filter(actif=True).prefetch_related())
        if not produits:
            return []

        # Calculer les features par produit
        ventes_par_produit = {
            v['produit_id']: v['total']
            for v in LigneCommande.objects.filter(
                commande__statut__in=['VALIDEE', 'LIVREE']
            ).values('produit_id').annotate(total=Sum('quantite'))
        }

        features = []
        produits_valides = []

        for p in produits:
            marge        = float(p.taux_marge) if p.prix_achat else 0
            volume       = float(ventes_par_produit.get(p.id, 0))
            stock_actuel = float(p.quantite)

            # Rotation : ventes / stock (éviter division par zéro)
            rotation = volume / (stock_actuel + 1)

            features.append([marge, volume, rotation])
            produits_valides.append(p)

        if len(features) < 4:
            # Pas assez de produits pour 4 clusters
            return self._classification_simple(produits_valides, ventes_par_produit)

        X = np.array(features)
        scaler  = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)

        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        # Identifier chaque cluster par ses caractéristiques moyennes
        centres   = scaler.inverse_transform(kmeans.cluster_centers_)
        # [marge_moy, volume_moy, rotation_moy] par cluster
        marge_moy  = centres[:, 0]
        volume_moy = centres[:, 1]

        marge_med  = np.median(marge_moy)
        volume_med = np.median(volume_moy)

        def _categoriser(cluster_id):
            m = marge_moy[cluster_id]
            v = volume_moy[cluster_id]
            if m >= marge_med and v >= volume_med:
                return 'STAR'
            if m >= marge_med and v < volume_med:
                return 'VACHE'
            if m < marge_med and v >= volume_med:
                return 'DILEMME'
            return 'POIDS_MORT'

        resultats = []
        for produit, label, feat in zip(produits_valides, labels, features):
            categorie = _categoriser(label)
            resultats.append({
                'produit_id':  produit.id,
                'nom':         produit.nom,
                'reference':   produit.reference,
                'taux_marge':  round(feat[0], 1),
                'volume':      round(feat[1], 1),
                'rotation':    round(feat[2], 2),
                'prix_vente':  float(produit.prix_vente),
                'stock':       float(produit.quantite),
                'categorie':   categorie,
                'emoji':       {'STAR':'⭐','VACHE':'🐄','DILEMME':'❓','POIDS_MORT':'💀'}[categorie],
                'conseil':     {
                    'STAR':       'Maintenir le stock — produit phare',
                    'VACHE':      'Bonne marge, fidéliser les clients actuels',
                    'DILEMME':    'Volume élevé mais marge faible — revoir le prix',
                    'POIDS_MORT': 'À liquider ou repositionner',
                }[categorie],
            })

        resultats.sort(key=lambda r: ['STAR','VACHE','DILEMME','POIDS_MORT'].index(r['categorie']))
        return resultats

    def _classification_simple(self, produits, ventes):
        """Fallback si moins de 4 produits : seuils manuels."""
        resultats = []
        for p in produits:
            marge  = float(p.taux_marge) if p.prix_achat else 0
            volume = float(ventes.get(p.id, 0))
            if marge >= 30 and volume >= 10:   cat = 'STAR'
            elif marge >= 30:                  cat = 'VACHE'
            elif volume >= 10:                 cat = 'DILEMME'
            else:                              cat = 'POIDS_MORT'
            resultats.append({
                'produit_id': p.id, 'nom': p.nom, 'reference': p.reference,
                'taux_marge': marge, 'volume': volume, 'rotation': 0,
                'prix_vente': float(p.prix_vente), 'stock': float(p.quantite),
                'categorie': cat,
                'emoji': {'STAR':'⭐','VACHE':'🐄','DILEMME':'❓','POIDS_MORT':'💀'}[cat],
                'conseil': {
                    'STAR': 'Maintenir le stock — produit phare',
                    'VACHE': 'Bonne marge, fidéliser les clients actuels',
                    'DILEMME': 'Volume élevé mais marge faible — revoir le prix',
                    'POIDS_MORT': 'À liquider ou repositionner',
                }[cat],
            })
        return resultats
