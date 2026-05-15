"""
web/views_achats.py
═════════════════════════════════════════════════════════════════════
Module Achats Fournisseur

  1. achats_liste()       — liste commandes achat avec filtres
  2. achat_nouveau()      — créer PO multi-lignes (cartons → pièces auto)
  3. achat_detail()       — détail PO + actions workflow
  4. achat_envoyer()      — BROUILLON → ENVOYEE
  5. achat_recevoir()     — ENVOYEE → RECUE
                           ✅ stock source déduit automatiquement
                           ✅ JournalFinancier ACHAT écrit (SORTIE)
                           ✅ MouvementStock ENTREE créé avec audit
  6. fournisseurs_liste() — annuaire fournisseurs
  7. fournisseur_nouveau()— créer un fournisseur
═════════════════════════════════════════════════════════════════════
"""
import logging
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from web.middleware import login_required_web, magasinier_or_admin, admin_required
from achats.models import Fournisseur, CommandeAchat, LigneAchat
from produits.models import Produit
from stock.models import Localisation, StockParLocalisation, MouvementStock
from finances.models import JournalFinancier

logger = logging.getLogger(__name__)


# ── Numérotation automatique ──────────────────────────────────────────────────
def _gen_reference():
    annee = date.today().strftime('%Y')
    mois  = date.today().strftime('%m')
    nb    = CommandeAchat.objects.filter(
        reference__startswith=f'PO-{annee}{mois}'
    ).count() + 1
    return f'PO-{annee}{mois}-{nb:04d}'


# ─────────────────────────────────────────────────────────────────────────────
# 1 — LISTE COMMANDES ACHAT
# ─────────────────────────────────────────────────────────────────────────────

@magasinier_or_admin
def achats_liste(request):
    qs = CommandeAchat.objects.select_related(
        'fournisseur', 'cree_par'
    ).order_by('-date_commande')

    statut = request.GET.get('statut', '')
    fourn  = request.GET.get('fourn', '')
    if statut: qs = qs.filter(statut=statut)
    if fourn:  qs = qs.filter(fournisseur_id=fourn)

    # KPIs
    total_gnf_mois = CommandeAchat.objects.filter(
        statut='RECUE',
        date_reception_reelle__month=date.today().month,
        date_reception_reelle__year=date.today().year,
    ).aggregate(t=Sum('total_gnf'))['t'] or 0

    return render(request, 'web/achats/liste.html', {
        'title':          'Commandes Achat',
        'achats':         qs[:100],
        'statuts':        CommandeAchat.STATUTS,
        'fournisseurs':   Fournisseur.objects.filter(actif=True).order_by('nom'),
        'filtre_statut':  statut,
        'filtre_fourn':   fourn,
        'total_gnf_mois': float(total_gnf_mois),
        'nb_en_attente':  CommandeAchat.objects.filter(statut='ENVOYEE').count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 2 — NOUVELLE COMMANDE ACHAT
# ─────────────────────────────────────────────────────────────────────────────

@magasinier_or_admin
def achat_nouveau(request):
    if request.method == 'GET':
        return render(request, 'web/achats/form.html', {
            'title':        'Nouvelle Commande Achat',
            'fournisseurs': Fournisseur.objects.filter(actif=True).order_by('nom'),
            'produits':     Produit.objects.filter(actif=True).order_by('nom'),
            'localisations':Localisation.objects.filter(actif=True),
            'devises':      Fournisseur.DEVISES,
            'today':        date.today().isoformat(),
        })

    with transaction.atomic():
        # ── En-tête PO ─────────────────────────────────────────────────────
        fourn_id    = request.POST.get('fournisseur_id')
        devise      = request.POST.get('devise', 'GNF')
        taux        = float(request.POST.get('taux_change', 1) or 1)
        date_cmd    = request.POST.get('date_commande') or date.today().isoformat()
        date_prev   = request.POST.get('date_reception_prevue') or None
        loc_id      = request.POST.get('localisation_id')
        notes       = request.POST.get('notes', '').strip()

        if not fourn_id:
            messages.error(request, 'Fournisseur obligatoire.')
            return redirect('web:achat_nouveau')

        fournisseur = get_object_or_404(Fournisseur, pk=fourn_id)

        # ── Lignes ─────────────────────────────────────────────────────────
        produits_noms  = request.POST.getlist('produit_nom')
        qtes_cartons   = request.POST.getlist('quantite_cartons')
        prix_devise    = request.POST.getlist('prix_unitaire_devise')

        if not produits_noms or not any(int(q or 0) > 0 for q in qtes_cartons):
            messages.error(request, 'Ajoutez au moins une ligne avec une quantité.')
            return redirect('web:achat_nouveau')

        achat = CommandeAchat.objects.create(
            reference=_gen_reference(),
            fournisseur=fournisseur,
            statut='BROUILLON',
            devise=devise,
            taux_change=taux,
            date_commande=date_cmd,
            date_reception_prevue=date_prev or None,
            cree_par=request.user,
            notes=notes,
        )

        # Stocker la localisation de réception dans les notes si pas de champ dédié
        if loc_id:
            achat.notes = (notes + f'\n[LOC:{loc_id}]').strip()
            achat.save(update_fields=['notes'])

        total_devise = 0
        for pnom, qte, prix in zip(produits_noms, qtes_cartons, prix_devise):
            qte  = int(qte or 0)
            prix = float(prix or 0)
            if qte <= 0 or not pnom:
                continue
            
            # Recherche du produit par Nom (REF) ou juste Nom ou REF
            import re
            m = re.search(r'\((.*?)\)', pnom)
            ref = m.group(1) if m else pnom
            
            produit = Produit.objects.filter(models.Q(reference=ref) | models.Q(nom=pnom.split(' (')[0])).first()
            
            if not produit:
                messages.warning(request, f"Produit '{pnom}' non trouvé, ligne ignorée.")
                continue
            ligne   = LigneAchat(
                achat=achat,
                produit=produit,
                quantite_cartons=qte,
                prix_unitaire_devise=prix,
            )
            ligne.save()   # save() calcule quantite_pieces + sous_totaux
            total_devise += float(ligne.sous_total_devise)

        # Totaux PO
        achat.total_devise = total_devise
        achat.total_gnf    = total_devise * taux
        achat.save(update_fields=['total_devise', 'total_gnf'])

    logger.info("[ACHAT] %s créé par %s", achat.reference, request.user.nom)
    messages.success(request, f'Commande achat {achat.reference} créée.')
    return redirect('web:achat_detail', pk=achat.pk)


# ─────────────────────────────────────────────────────────────────────────────
# 3 — DÉTAIL COMMANDE ACHAT
# ─────────────────────────────────────────────────────────────────────────────

@magasinier_or_admin
def achat_detail(request, pk):
    achat  = get_object_or_404(
        CommandeAchat.objects.select_related('fournisseur', 'cree_par'), pk=pk
    )
    lignes = achat.lignes.select_related('produit').all()

    # Extraire localisation des notes si présente
    loc_id = None
    if achat.notes and '[LOC:' in achat.notes:
        import re
        m = re.search(r'\[LOC:(\d+)\]', achat.notes)
        if m:
            loc_id = m.group(1)

    loc = Localisation.objects.filter(pk=loc_id).first() if loc_id else \
          Localisation.objects.filter(type='MAGASIN').first()

    return render(request, 'web/achats/detail.html', {
        'title':        f'PO — {achat.reference}',
        'achat':        achat,
        'lignes':       lignes,
        'loc':          loc,
        'localisations':Localisation.objects.filter(actif=True),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 4 — ENVOYER AU FOURNISSEUR : BROUILLON → ENVOYEE
# ─────────────────────────────────────────────────────────────────────────────

@magasinier_or_admin
def achat_envoyer(request, pk):
    achat = get_object_or_404(CommandeAchat, pk=pk)

    if achat.statut != 'BROUILLON':
        messages.error(request, 'Seul un brouillon peut être envoyé.')
        return redirect('web:achat_detail', pk=pk)

    achat.statut = 'ENVOYEE'
    achat.save(update_fields=['statut'])

    messages.success(request, f'{achat.reference} marquée comme envoyée au fournisseur.')
    return redirect('web:achat_detail', pk=pk)


# ─────────────────────────────────────────────────────────────────────────────
# 5 — RÉCEPTIONNER : ENVOYEE → RECUE + stock auto + journal ACHAT
# ─────────────────────────────────────────────────────────────────────────────

@magasinier_or_admin
@transaction.atomic
def achat_recevoir(request, pk):
    """
    Réception complète :
    ✅ Statut → RECUE
    ✅ StockParLocalisation += quantite_pieces pour chaque ligne
    ✅ MouvementStock ENTREE créé (avec quantite_avant / quantite_apres)
    ✅ Produit.quantite globale recalculée
    ✅ JournalFinancier ACHAT SORTIE créé (immuable)
    """
    achat = get_object_or_404(
        CommandeAchat.objects.select_related('fournisseur'), pk=pk
    )

    if achat.statut != 'ENVOYEE':
        messages.error(
            request,
            f'Impossible de réceptionner : statut actuel "{achat.get_statut_display()}".'
        )
        return redirect('web:achat_detail', pk=pk)

    # Localisation de réception (depuis le formulaire ou les notes)
    loc_id = request.POST.get('localisation_id')
    if not loc_id and achat.notes and '[LOC:' in achat.notes:
        import re
        m = re.search(r'\[LOC:(\d+)\]', achat.notes)
        if m:
            loc_id = m.group(1)

    loc = Localisation.objects.filter(pk=loc_id).first() \
          if loc_id else Localisation.objects.filter(type='MAGASIN').first()

    if not loc:
        messages.error(request, 'Localisation de réception introuvable. Configurez un site MAGASIN.')
        return redirect('web:achat_detail', pk=pk)

    lignes = achat.lignes.select_related('produit').all()

    # ── Mise à jour stock par ligne ───────────────────────────────────────────
    for ligne in lignes:
        stock, _ = StockParLocalisation.objects.select_for_update().get_or_create(
            produit=ligne.produit,
            localisation=loc,
            defaults={'quantite': 0},
        )
        avant = stock.quantite
        stock.quantite += ligne.quantite_pieces
        stock.save()

        # Mouvement ENTREE avec snapshot audit
        MouvementStock.objects.create(
            produit=ligne.produit,
            localisation=loc,
            type='ENTREE',
            quantite=ligne.quantite_pieces,
            quantite_avant=avant,
            quantite_apres=stock.quantite,
            reference_doc=achat.reference,
            utilisateur=request.user,
            notes=(
                f'Réception PO {achat.reference} — '
                f'{ligne.quantite_cartons} carton(s) × {ligne.produit.conversion_unit} '
                f'= {ligne.quantite_pieces} pcs @ {loc.nom}'
            ),
        )

        # Recalcul quantite globale produit
        total_global = StockParLocalisation.objects.filter(
            produit=ligne.produit
        ).aggregate(t=Sum('quantite'))['t'] or 0
        ligne.produit.quantite = total_global
        ligne.produit.save(update_fields=['quantite'])

        logger.info(
            "[STOCK] +%d pcs %s @ %s (PO %s)",
            ligne.quantite_pieces, ligne.produit.nom, loc.nom, achat.reference
        )

    # ── Journal ACHAT — SORTIE immuable ──────────────────────────────────────
    from django.utils import timezone as tz
    import uuid

    JournalFinancier.objects.create(
        type_operation='ACHAT',
        reference_doc=achat.reference,
        description=(
            f'Achat fournisseur {achat.fournisseur.nom} — '
            f'{lignes.count()} ref(s) — '
            f'{float(achat.total_devise):,.2f} {achat.devise}'
        ),
        montant=achat.total_gnf,
        devise=achat.devise,
        taux=achat.taux_change,
        montant_gnf=achat.total_gnf,
        type_flux='SORTIE',
        utilisateur=request.user,
    )

    # ── Finaliser la commande achat ───────────────────────────────────────────
    achat.statut               = 'RECUE'
    achat.date_reception_reelle = tz.now()
    achat.save(update_fields=['statut', 'date_reception_reelle'])

    logger.info(
        "[ACHAT] %s réceptionnée par %s → %s",
        achat.reference, request.user.nom, loc.nom
    )
    messages.success(
        request,
        f'✅ {achat.reference} réceptionnée — '
        f'{lignes.count()} produit(s) mis en stock à {loc.nom}. '
        f'Journal financier mis à jour.'
    )
    return redirect('web:achat_detail', pk=pk)


# ─────────────────────────────────────────────────────────────────────────────
# 6 — LISTE FOURNISSEURS
# ─────────────────────────────────────────────────────────────────────────────

@magasinier_or_admin
def fournisseurs_liste(request):
    fournisseurs = Fournisseur.objects.annotate(
        nb_achats=Sum('achats__id')
    ).order_by('nom')

    return render(request, 'web/achats/fournisseurs.html', {
        'title':        'Fournisseurs',
        'fournisseurs': fournisseurs,
        'types':        Fournisseur.TYPES,
    })


# ─────────────────────────────────────────────────────────────────────────────
# 7 — NOUVEAU FOURNISSEUR
# ─────────────────────────────────────────────────────────────────────────────

@magasinier_or_admin
def fournisseur_nouveau(request):
    if request.method == 'GET':
        return render(request, 'web/achats/fournisseur_form.html', {
            'title':   'Nouveau Fournisseur',
            'types':   Fournisseur.TYPES,
            'devises': Fournisseur.DEVISES,
        })

    nom    = request.POST.get('nom', '').strip()
    pays   = request.POST.get('pays', 'Guinée').strip()
    type_f = request.POST.get('type', 'LOCAL')
    devise = request.POST.get('devise_par_defaut', 'GNF')
    tel    = request.POST.get('telephone', '').strip() or None
    email  = request.POST.get('email', '').strip() or None
    adresse= request.POST.get('adresse', '').strip() or None

    if not nom:
        messages.error(request, 'Le nom est obligatoire.')
        return redirect('web:fournisseur_nouveau')

    if Fournisseur.objects.filter(nom__iexact=nom).exists():
        messages.error(request, f'Un fournisseur nommé "{nom}" existe déjà.')
        return redirect('web:fournisseur_nouveau')

    Fournisseur.objects.create(
        nom=nom, pays=pays, type=type_f,
        devise_par_defaut=devise,
        telephone=tel, email=email, adresse=adresse,
    )
    messages.success(request, f'Fournisseur {nom} créé.')
    return redirect('web:fournisseurs_liste')
