"""
web/views_import_modele.py
Génère et télécharge le modèle CSV vierge pour l'import produits.
"""
import csv
from django.http import HttpResponse
from web.middleware import admin_required


@admin_required
def telecharger_modele_csv(request):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="modele_produits.csv"'

    writer = csv.writer(response)

    # En-têtes
    writer.writerow([
        'nom', 'reference', 'prix_vente',
        'prix_achat', 'seuil_alerte', 'categorie', 'description'
    ])

    # 3 exemples pour guider l'utilisateur
    writer.writerow([
        'Filtre à huile X200', 'FH-X200-12', '45000',
        '32000', '5', 'Filtration', 'Compatible Toyota Corolla 2015-2020'
    ])
    writer.writerow([
        'Plaquette frein avant Y300', 'PF-Y300-AV', '85000',
        '58000', '3', 'Freinage', 'Kit 4 plaquettes'
    ])
    writer.writerow([
        'Courroie distribution Z50', 'CD-Z50-STD', '120000',
        '85000', '2', 'Distribution', 'Longueur 120cm'
    ])

    return response
