"""
web/views_assistant.py
Assistant IA BSG — langage naturel connecté aux données réelles.

Fonctionnement :
  1. L'utilisateur pose une question en français
  2. Le moteur analyse les mots-clés pour déterminer le type de requête
  3. Les données correspondantes sont extraites depuis Django
  4. Une réponse structurée est générée et retournée en JSON
  5. Tout s'exécute localement — aucun appel API externe

Questions supportées :
  - "Quel est mon profit ce mois ?"
  - "Qui sont mes meilleurs clients ?"
  - "Quels produits sont en rupture ?"
  - "Combien j'ai vendu cette semaine ?"
  - "Quelles sont mes dépenses ?"
  - "Quel est mon stock de [produit] ?"
  - "Montre-moi les commandes en attente"
  - "Quelle est ma dette client totale ?"
"""
import logging
import re
from datetime import date, timedelta
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Q
from django.utils import timezone

from web.middleware import login_required_web

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MOTEUR DE COMPRÉHENSION — analyse les intentions
# ─────────────────────────────────────────────────────────────────────────────

def _detecter_periode(question):
    q = question.lower()
    if any(w in q for w in ["aujourd'hui", "aujourd", "ce jour", "journee"]):
        debut = fin = date.today()
        label = "aujourd'hui"
    elif any(w in q for w in ["semaine", "cette semaine", "7 jours"]):
        debut = date.today() - timedelta(days=date.today().weekday())
        fin   = date.today()
        label = "cette semaine"
    elif any(w in q for w in ["mois", "ce mois", "mensuel"]):
        debut = date.today().replace(day=1)
        fin   = date.today()
        label = "ce mois"
    elif any(w in q for w in ["annee", "année", "annuel", "cette année"]):
        debut = date.today().replace(month=1, day=1)
        fin   = date.today()
        label = "cette année"
    elif any(w in q for w in ["trimestre"]):
        mois_debut = ((date.today().month - 1) // 3) * 3 + 1
        debut = date.today().replace(month=mois_debut, day=1)
        fin   = date.today()
        label = "ce trimestre"
    else:
        debut = date.today().replace(day=1)
        fin   = date.today()
        label = "ce mois"
    return debut, fin, label


def _detecter_intention(question):
    q = question.lower()
    mots = {
        'profit':     ['profit', 'bénéfice', 'benefice', 'marge', 'gain', 'résultat', 'resultat'],
        'ventes':     ['vente', 'vendu', 'commande', 'ca', "chiffre d'affaires", 'encaissement', 'paiement'],
        'stock':      ['stock', 'inventaire', 'rupture', 'alerte', 'quantite', 'disponible'],
        'depenses':   ['depense', 'dépense', 'charge', 'sortie', 'frais', 'coût', 'cout'],
        'clients':    ['client', 'meilleur', 'dette', 'debiteur', 'acheteur'],
        'commandes':  ['commande', 'attente', 'livraison', 'expedition', 'en cours'],
        'produits':   ['produit', 'article', 'reference', 'catalogue'],
        'fournisseurs': ['fournisseur', 'achat', 'approvisionnement'],
        'aide':       ['aide', 'que peux', 'que puis', 'quoi', 'comment', 'bonjour', 'salut', 'hello'],
    }
    scores = {intention: 0 for intention in mots}
    for intention, keywords in mots.items():
        for kw in keywords:
            if kw in q:
                scores[intention] += 1
    return max(scores, key=scores.get)


# ─────────────────────────────────────────────────────────────────────────────
# HANDLERS PAR INTENTION
# ─────────────────────────────────────────────────────────────────────────────

def _repondre_profit(debut, fin, label, question):
    from finances.models import JournalFinancier
    totaux = JournalFinancier.objects.filter(
        created_at__date__gte=debut, created_at__date__lte=fin
    ).aggregate(
        entrees=Sum('montant_gnf', filter=Q(type_flux='ENTREE')),
        sorties=Sum('montant_gnf', filter=Q(type_flux='SORTIE')),
    )
    entrees = float(totaux['entrees'] or 0)
    sorties = float(totaux['sorties'] or 0)
    profit  = entrees - sorties

    emoji   = '📈' if profit >= 0 else '📉'
    couleur = 'success' if profit >= 0 else 'danger'

    return {
        'type':    'profit',
        'titre':   f'{emoji} Profit {label}',
        'couleur': couleur,
        'resume':  f"Votre profit net {label} est de **{profit:,.0f} GNF**.",
        'details': [
            {'label': 'Encaissements', 'valeur': f'{entrees:,.0f} GNF', 'couleur': 'success'},
            {'label': 'Dépenses',      'valeur': f'{sorties:,.0f} GNF', 'couleur': 'danger'},
            {'label': 'Profit net',    'valeur': f'{profit:,.0f} GNF',  'couleur': couleur},
        ],
        'action': {'label': 'Voir le journal', 'url': '/finances/rapport/'},
    }


def _repondre_ventes(debut, fin, label, question):
    from commandes.models import Commande
    from finances.models import JournalFinancier

    nb_cmd = Commande.objects.filter(
        date_creation__date__gte=debut, date_creation__date__lte=fin,
        statut__in=['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE']
    ).count()

    total_enc = float(JournalFinancier.objects.filter(
        created_at__date__gte=debut, created_at__date__lte=fin,
        type_flux='ENTREE', type_operation__in=['VENTE', 'PAIEMENT']
    ).aggregate(t=Sum('montant_gnf'))['t'] or 0)

    return {
        'type':    'ventes',
        'titre':   f'🛒 Ventes {label}',
        'couleur': 'primary',
        'resume':  f"**{nb_cmd} commandes** traitées {label} pour un total de **{total_enc:,.0f} GNF**.",
        'details': [
            {'label': 'Commandes',     'valeur': str(nb_cmd),            'couleur': 'primary'},
            {'label': 'Encaissements', 'valeur': f'{total_enc:,.0f} GNF', 'couleur': 'success'},
        ],
        'action': {'label': 'Voir les commandes', 'url': '/commandes/'},
    }


def _repondre_stock(debut, fin, label, question):
    from produits.models import Produit
    from stock.models import StockParLocalisation

    ruptures = StockParLocalisation.objects.filter(quantite=0).count()
    alertes  = Produit.objects.filter(est_en_alerte=True, actif=True).count()
    total_p  = Produit.objects.filter(actif=True).count()

    # Chercher un produit spécifique dans la question
    produit_nom = None
    from produits.models import Produit as P
    for p in P.objects.filter(actif=True).values('nom', 'quantite', 'reference', 'id'):
        if p['nom'].lower() in question.lower() or p['reference'].lower() in question.lower():
            produit_nom = p
            break

    if produit_nom:
        return {
            'type':    'stock',
            'titre':   f'📦 Stock — {produit_nom["nom"]}',
            'couleur': 'success' if produit_nom['quantite'] > 0 else 'danger',
            'resume':  f"Le stock de **{produit_nom['nom']}** est de **{produit_nom['quantite']} unités**.",
            'details': [
                {'label': 'Référence', 'valeur': produit_nom['reference'], 'couleur': 'secondary'},
                {'label': 'Stock',     'valeur': str(produit_nom['quantite']),
                 'couleur': 'success' if produit_nom['quantite'] > 5 else 'danger'},
            ],
            'action': {'label': "Voir l'inventaire", 'url': '/stock/'},
        }

    return {
        'type':    'stock',
        'titre':   '📦 État du Stock',
        'couleur': 'danger' if ruptures > 0 else 'success',
        'resume':  f"**{total_p} produits** actifs. **{ruptures} ruptures** et **{alertes} alertes** en ce moment.",
        'details': [
            {'label': 'Produits actifs', 'valeur': str(total_p),  'couleur': 'primary'},
            {'label': 'Ruptures',        'valeur': str(ruptures), 'couleur': 'danger'},
            {'label': 'Alertes stock',   'valeur': str(alertes),  'couleur': 'warning'},
        ],
        'action': {'label': 'Voir les alertes', 'url': '/admin/alertes-stock/'},
    }


def _repondre_depenses(debut, fin, label, question):
    from finances.models import Depense
    totaux = Depense.objects.filter(
        date_depense__date__gte=debut, date_depense__date__lte=fin
    ).aggregate(
        total=Sum('montant_gnf'),
        pro=Sum('montant_gnf', filter=Q(type_depense='ENTREPRISE')),
        perso=Sum('montant_gnf', filter=Q(type_depense='PERSONNEL')),
    )
    total = float(totaux['total'] or 0)
    pro   = float(totaux['pro']   or 0)
    perso = float(totaux['perso'] or 0)

    return {
        'type':    'depenses',
        'titre':   f'💸 Dépenses {label}',
        'couleur': 'danger',
        'resume':  f"Total des dépenses {label} : **{total:,.0f} GNF** (Pro: {pro:,.0f} | Perso: {perso:,.0f}).",
        'details': [
            {'label': 'Total',           'valeur': f'{total:,.0f} GNF', 'couleur': 'danger'},
            {'label': 'Professionnelles', 'valeur': f'{pro:,.0f} GNF',  'couleur': 'primary'},
            {'label': 'Personnelles',    'valeur': f'{perso:,.0f} GNF', 'couleur': 'warning'},
        ],
        'action': {'label': 'Voir les dépenses', 'url': '/finances/depenses/'},
    }


def _repondre_clients(debut, fin, label, question):
    from clients.models import Client
    from commandes.models import Commande

    total_dette = float(Client.objects.filter(actif=True).aggregate(
        t=Sum('total_dette'))['t'] or 0)
    nb_debiteurs = Client.objects.filter(actif=True, total_dette__gt=0).count()

    top = list(Commande.objects.filter(
        date_creation__date__gte=debut, date_creation__date__lte=fin,
        client__isnull=False, statut__in=['VALIDEE', 'LIVREE']
    ).values('client__nom').annotate(
        total=Sum('total_ttc')
    ).order_by('-total')[:3])

    details = [
        {'label': 'Dettes clients', 'valeur': f'{total_dette:,.0f} GNF', 'couleur': 'danger'},
        {'label': 'Clients débiteurs', 'valeur': str(nb_debiteurs), 'couleur': 'warning'},
    ]
    if top:
        details.append({'label': f"Top client — {top[0]['client__nom']}",
                        'valeur': f"{float(top[0]['total']):,.0f} GNF", 'couleur': 'success'})

    return {
        'type':    'clients',
        'titre':   f'👥 Clients {label}',
        'couleur': 'primary',
        'resume':  f"**{nb_debiteurs} clients** ont des dettes. Total impayé : **{total_dette:,.0f} GNF**.",
        'details': details,
        'action': {'label': 'Rapport dettes', 'url': '/clients/rapport-dettes/'},
    }


def _repondre_commandes(debut, fin, label, question):
    from commandes.models import Commande
    statuts = Commande.objects.values('statut').annotate(nb=Count('id'))
    details = [
        {'label': s['statut'].replace('_', ' '), 'valeur': str(s['nb']), 'couleur': 'secondary'}
        for s in statuts
    ]
    nb_att = Commande.objects.filter(statut='EN_ATTENTE').count()
    return {
        'type':    'commandes',
        'titre':   '📋 État des Commandes',
        'couleur': 'warning' if nb_att > 0 else 'success',
        'resume':  f"**{nb_att} commande(s)** en attente de validation.",
        'details': details[:5],
        'action': {'label': 'Voir les commandes', 'url': '/commandes/'},
    }


def _repondre_aide(question):
    return {
        'type':    'aide',
        'titre':   '🤖 Assistant BSG',
        'couleur': 'primary',
        'resume':  "Bonjour ! Je suis votre assistant BSG. Voici ce que vous pouvez me demander :",
        'details': [
            {'label': 'Finances',   'valeur': '"Quel est mon profit ce mois ?"',         'couleur': 'success'},
            {'label': 'Ventes',     'valeur': '"Combien j\'ai vendu cette semaine ?"',   'couleur': 'primary'},
            {'label': 'Stock',      'valeur': '"Quels produits sont en rupture ?"',      'couleur': 'warning'},
            {'label': 'Dépenses',   'valeur': '"Quelles sont mes dépenses ce mois ?"',  'couleur': 'danger'},
            {'label': 'Clients',    'valeur': '"Qui sont mes meilleurs clients ?"',      'couleur': 'info'},
            {'label': 'Commandes',  'valeur': '"Montre les commandes en attente"',       'couleur': 'secondary'},
        ],
        'action': None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# VUE PRINCIPALE
# ─────────────────────────────────────────────────────────────────────────────

@login_required_web
def assistant_view(request):
    return render(request, 'web/ia/assistant.html', {
        'title': 'Assistant IA BSG',
    })


@login_required_web
@require_POST
def assistant_query(request):
    import json
    try:
        body     = json.loads(request.body)
        question = body.get('question', '').strip()
    except Exception:
        question = request.POST.get('question', '').strip()

    if not question:
        return JsonResponse({'erreur': 'Question vide.'}, status=400)

    if len(question) > 300:
        question = question[:300]

    logger.info("[ASSISTANT] Question de %s : %s", request.user.nom, question)

    debut, fin, label = _detecter_periode(question)
    intention         = _detecter_intention(question)

    try:
        handlers = {
            'profit':       _repondre_profit,
            'ventes':       _repondre_ventes,
            'stock':        _repondre_stock,
            'depenses':     _repondre_depenses,
            'clients':      _repondre_clients,
            'commandes':    _repondre_commandes,
            'produits':     _repondre_stock,
            'fournisseurs': lambda d, f, l, q: _repondre_aide(q),
            'aide':         lambda d, f, l, q: _repondre_aide(q),
        }
        handler  = handlers.get(intention, lambda d, f, l, q: _repondre_aide(q))
        reponse  = handler(debut, fin, label, question)
        reponse['question'] = question
        return JsonResponse({'ok': True, 'reponse': reponse})

    except Exception as e:
        logger.error("[ASSISTANT] Erreur : %s", e)
        return JsonResponse({
            'ok': True,
            'reponse': {
                'type':    'erreur',
                'titre':   '⚠ Erreur',
                'couleur': 'warning',
                'resume':  f"Je n'ai pas pu traiter votre demande. Essayez de reformuler.",
                'details': [],
                'action':  None,
                'question': question,
            }
        })
