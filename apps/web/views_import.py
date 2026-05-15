"""
web/views_import.py
Import produits en masse depuis CSV ou Excel.
Valide chaque ligne et retourne un rapport détaillé.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from web.middleware import admin_required

logger = logging.getLogger(__name__)

COLONNES_REQUISES = ['nom', 'reference', 'prix_vente']
COLONNES_OPT     = ['prix_achat', 'seuil_alerte', 'description', 'categorie', 'unite']


@admin_required
def import_produits(request):
    if request.method == 'GET':
        return render(request, 'web/admin/import_produits.html', {
            'title':    'Import Produits',
            'colonnes': COLONNES_REQUISES + COLONNES_OPT,
        })

    fichier = request.FILES.get('fichier')
    if not fichier:
        messages.error(request, 'Aucun fichier sélectionné.')
        return redirect('web:import_produits')

    nom = fichier.name.lower()
    try:
        if nom.endswith('.csv'):
            lignes = _lire_csv(fichier)
        elif nom.endswith(('.xlsx', '.xls')):
            lignes = _lire_excel(fichier)
        else:
            messages.error(request, 'Format non supporté. Utilisez .csv ou .xlsx')
            return redirect('web:import_produits')
    except Exception as e:
        messages.error(request, f'Erreur lecture fichier : {e}')
        return redirect('web:import_produits')

    resultats = _importer(lignes)

    return render(request, 'web/admin/import_resultats.html', {
        'title':    'Résultats Import',
        'resultats': resultats,
        'nb_ok':    sum(1 for r in resultats if r['statut'] == 'OK'),
        'nb_err':   sum(1 for r in resultats if r['statut'] == 'ERREUR'),
        'nb_skip':  sum(1 for r in resultats if r['statut'] == 'DOUBLON'),
    })


def _lire_csv(fichier):
    import csv, io
    content = fichier.read().decode('utf-8-sig')
    reader  = csv.DictReader(io.StringIO(content), delimiter=',')
    return list(reader)


def _lire_excel(fichier):
    import openpyxl
    wb   = openpyxl.load_workbook(fichier, data_only=True)
    ws   = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    headers = [str(h).strip().lower() if h else '' for h in rows[0]]
    lignes  = []
    for row in rows[1:]:
        if all(v is None for v in row):
            continue
        lignes.append({headers[i]: (str(v).strip() if v is not None else '') for i, v in enumerate(row)})
    return lignes


def _importer(lignes):
    from produits.models import Produit, Categorie
    resultats = []

    for i, ligne in enumerate(lignes, 1):
        row = {k.lower().strip(): v for k, v in ligne.items()}

        # ── Validation obligatoires ────────────────────────────────────────
        erreurs = []
        nom       = row.get('nom', '').strip()
        reference = row.get('reference', '').strip()
        prix_str  = row.get('prix_vente', '').strip()

        if not nom:       erreurs.append('nom manquant')
        if not reference: erreurs.append('référence manquante')
        if not prix_str:  erreurs.append('prix_vente manquant')

        try:
            prix_vente = float(prix_str.replace(' ', '').replace(',', '.')) if prix_str else 0
            if prix_vente < 0: erreurs.append('prix_vente négatif')
        except ValueError:
            erreurs.append(f'prix_vente invalide : "{prix_str}"')
            prix_vente = 0

        if erreurs:
            resultats.append({'ligne': i, 'nom': nom or '—',
                              'reference': reference or '—',
                              'statut': 'ERREUR', 'message': ' | '.join(erreurs)})
            continue

        # ── Doublon référence ──────────────────────────────────────────────
        if Produit.objects.filter(reference=reference).exists():
            resultats.append({'ligne': i, 'nom': nom, 'reference': reference,
                              'statut': 'DOUBLON', 'message': 'Référence déjà existante — ignorée'})
            continue

        # ── Champs optionnels ──────────────────────────────────────────────
        try:
            prix_achat = float(row.get('prix_achat', '0').replace(',', '.') or 0)
        except ValueError:
            prix_achat = 0

        try:
            seuil = int(row.get('seuil_alerte', '5') or 5)
        except ValueError:
            seuil = 5

        categorie = None
        cat_nom   = row.get('categorie', '').strip()
        if cat_nom:
            categorie, _ = Categorie.objects.get_or_create(nom=cat_nom)

        # ── Création ──────────────────────────────────────────────────────
        try:
            Produit.objects.create(
                nom=nom,
                reference=reference,
                prix_vente=prix_vente,
                prix_achat=prix_achat,
                seuil_alerte=seuil,
                description=row.get('description', '').strip(),
                categorie=categorie,
                actif=True,
            )
            resultats.append({'ligne': i, 'nom': nom, 'reference': reference,
                              'statut': 'OK', 'message': 'Créé avec succès'})
            logger.info("[IMPORT] Produit créé : %s (%s)", nom, reference)

        except Exception as e:
            resultats.append({'ligne': i, 'nom': nom, 'reference': reference,
                              'statut': 'ERREUR', 'message': str(e)[:100]})

    return resultats
