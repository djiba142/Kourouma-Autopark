"""
web/views_stock.py
Gestion de l'inventaire et des transferts inter-dépôts.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from web.middleware import magasinier_or_admin, login_required_web
from produits.models import Produit
from stock.models import Localisation, StockParLocalisation, MouvementStock, TransfertStock, TransfertItem


@magasinier_or_admin
def stock_liste(request):
    """Liste globale du stock filtrable par localisation."""
    loc_id = request.GET.get('loc')
    stocks = StockParLocalisation.objects.select_related('produit', 'localisation').all()
    
    if loc_id:
        stocks = stocks.filter(localisation_id=loc_id)
        
    return render(request, 'web/stock/liste.html', {
        'title': 'Inventaire',
        'stocks': stocks.order_by('produit__nom'),
        'localisations': Localisation.objects.filter(actif=True),
        'loc_id': int(loc_id) if loc_id else None
    })


@magasinier_or_admin
@transaction.atomic
def stock_entree(request):
    """Enregistrement manuel d'une entrée en stock (hors achat) ou import en masse."""
    if request.method == 'POST':
        loc_id = request.POST.get('localisation_id')
        loc = get_object_or_404(Localisation, pk=loc_id)
        
        fichier = request.FILES.get('fichier')
        
        if fichier:
            # Traitement Import Fichier
            from web.views_import import _lire_csv, _lire_excel
            nom_fichier = fichier.name.lower()
            try:
                if nom_fichier.endswith('.csv'):
                    lignes = _lire_csv(fichier)
                elif nom_fichier.endswith(('.xlsx', '.xls')):
                    lignes = _lire_excel(fichier)
                else:
                    messages.error(request, 'Format non supporté. Utilisez .csv ou .xlsx')
                    return redirect('web:stock_entree')
            except Exception as e:
                messages.error(request, f"Erreur lecture fichier : {e}")
                return redirect('web:stock_entree')
                
            succes = 0
            erreurs = 0
            for ligne in lignes:
                row = {k.lower().strip(): v for k, v in ligne.items()}
                ref = row.get('reference', '').strip()
                qte_str = row.get('quantite', '').strip()
                
                if not ref or not qte_str:
                    erreurs += 1
                    continue
                    
                try:
                    qte = int(float(str(qte_str).replace(',', '.')))
                    if qte <= 0:
                        erreurs += 1
                        continue
                except ValueError:
                    erreurs += 1
                    continue
                    
                produit = Produit.objects.filter(reference=ref).first()
                if not produit:
                    erreurs += 1
                    continue
                    
                # Mise à jour stock
                stock, _ = StockParLocalisation.objects.get_or_create(produit=produit, localisation=loc)
                stock.quantite += qte
                stock.save()
                
                # Log mouvement
                MouvementStock.objects.create(
                    produit=produit, localisation=loc, type='ENTREE',
                    quantite=qte, utilisateur=request.user, notes=f"Import {fichier.name}"
                )
                succes += 1
                
            if succes > 0:
                messages.success(request, f"{succes} produits mis à jour avec succès dans {loc.nom}.")
            if erreurs > 0:
                messages.warning(request, f"{erreurs} lignes ignorées (référence introuvable ou quantité invalide).")
                
            return redirect('web:stock_liste')
            
        else:
            # Traitement Saisie Manuelle
            p_id = request.POST.get('produit_id')
            qte_str = request.POST.get('quantite')
            ref_mvt = request.POST.get('reference', 'Entrée manuelle web')
            
            if not p_id or not qte_str:
                messages.error(request, "Veuillez sélectionner un produit et indiquer une quantité.")
                return redirect('web:stock_entree')
                
            qte = int(qte_str)
            produit = get_object_or_404(Produit, pk=p_id)
            
            # Mise à jour stock
            stock, _ = StockParLocalisation.objects.get_or_create(produit=produit, localisation=loc)
            stock.quantite += qte
            stock.save()
            
            # Log mouvement
            MouvementStock.objects.create(
                produit=produit, localisation=loc, type='ENTREE',
                quantite=qte, utilisateur=request.user, notes=ref_mvt
            )
            
            messages.success(request, f"Stock mis à jour pour {produit.nom} dans {loc.nom}.")
            return redirect('web:stock_liste')

    return render(request, 'web/stock/entree.html', {
        'title': 'Entrée Stock',
        'produits': Produit.objects.filter(actif=True),
        'localisations': Localisation.objects.filter(actif=True)
    })


@magasinier_or_admin
def transferts_liste(request):
    return render(request, 'web/stock/transferts.html', {
        'title': 'Transferts',
        'transferts': TransfertStock.objects.order_by('-date_creation')[:50],
        'statuts': TransfertStock.STATUTS
    })


@magasinier_or_admin
@transaction.atomic
def transfert_nouveau(request):
    if request.method == 'POST':
        prov_id = request.POST.get('provenance_id')
        dest_id = request.POST.get('destination_id')
        
        import uuid
        trf = TransfertStock.objects.create(
            reference=f"TRF-{uuid.uuid4().hex[:6].upper()}",
            provenance_id=prov_id, destination_id=dest_id,
            cree_par=request.user, statut='PROPOSE'
        )
        
        # On peut imaginer ici une gestion de lignes multiples en JS
        # Pour cet exemple on simplifie
        p_id = request.POST.get('produit_id')
        qte  = int(request.POST.get('quantite', 0))
        TransfertItem.objects.create(transfert=trf, produit_id=p_id, quantite_demandee=qte)
        
        messages.success(request, "Transfert initialisé.")
        return redirect('web:transferts_liste')

    return render(request, 'web/stock/transfert_form.html', {
        'title': 'Nouveau transfert',
        'produits': Produit.objects.filter(actif=True),
        'localisations': Localisation.objects.filter(actif=True)
    })


@magasinier_or_admin
def transfert_expedier(request, pk):
    trf = get_object_or_404(TransfertStock, pk=pk)
    trf.statut = 'EXPEDIE'
    trf.save()
    messages.success(request, "Transfert marqué comme expédié.")
    return redirect('web:transferts_liste')


@magasinier_or_admin
def transfert_recevoir(request, pk):
    trf = get_object_or_404(TransfertStock, pk=pk)
    trf.statut = 'RECU'
    trf.save()
    messages.success(request, "Transfert réceptionné.")
    return redirect('web:transferts_liste')
