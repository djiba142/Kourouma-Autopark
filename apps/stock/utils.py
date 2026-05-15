"""
Utilitaires pour export et gestion stock
"""
import csv
from io import StringIO
from django.http import HttpResponse
from datetime import datetime
from .models import MouvementStock


def export_mouvements_csv(queryset=None, response=None):
    """
    Exporte les mouvements de stock en CSV
    """
    if queryset is None:
        queryset = MouvementStock.objects.all()
    
    if response is None:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="mouvements_stock_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response, delimiter=';')
    
    # En-tête
    writer.writerow([
        'Date', 'Type Mouvement', 'Produit', 'Référence', 'Localisation',
        'Quantité', 'Stock Avant', 'Stock Après', 'Utilisateur', 'Référence Doc', 'Notes'
    ])
    
    # Données
    for mouvement in queryset:
        writer.writerow([
            mouvement.date.strftime('%d/%m/%Y %H:%M:%S'),
            mouvement.get_type_display(),
            mouvement.produit.nom,
            mouvement.produit.reference,
            mouvement.localisation.nom if mouvement.localisation else '-',
            mouvement.quantite,
            mouvement.quantite_avant,
            mouvement.quantite_apres,
            mouvement.utilisateur.username if mouvement.utilisateur else '-',
            mouvement.reference_doc or '-',
            mouvement.notes or '-'
        ])
    
    return response


def obtenir_alertes_stock():
    """
    Retourne dict avec alertes stock
    """
    from .models import StockParLocalisation
    
    alertes = StockParLocalisation.objects.filter(
        quantite__lte=models.F('produit__seuil_alerte')
    ).select_related('produit', 'localisation')
    
    return {
        'total_alertes': alertes.count(),
        'ruptures': alertes.filter(quantite=0).count(),
        'en_alerte': alertes.filter(quantite__gt=0).count(),
        'details': alertes
    }


def calculer_valeur_stock(localisation=None):
    """
    Calcule la valeur totale du stock
    """
    from .models import StockParLocalisation
    
    qs = StockParLocalisation.objects.all()
    if localisation:
        qs = qs.filter(localisation=localisation)
    
    total = 0
    for item in qs:
        total += float(item.quantite) * float(item.produit.prix_achat)
    
    return total
