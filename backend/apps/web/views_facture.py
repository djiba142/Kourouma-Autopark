"""
web/views_facture.py
Génération de factures PDF professionnelles avec WeasyPrint.
"""
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from web.middleware import login_required_web
from commandes.models import Commande


@login_required_web
def facture_pdf(request, pk):
    commande = get_object_or_404(
        Commande.objects.select_related('client', 'cree_par')
                       .prefetch_related('lignes__produit', 'paiements'),
        pk=pk
    )

    total_paye = sum(float(p.montant) for p in commande.paiements.all())
    reste      = float(commande.total_ttc) - total_paye

    html = render_to_string('web/facture/facture_pdf.html', {
        'commande':    commande,
        'lignes':      commande.lignes.select_related('produit').all(),
        'paiements':   commande.paiements.all(),
        'total_paye':  total_paye,
        'reste':       reste,
    }, request=request)

    try:
        from weasyprint import HTML, CSS
        pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'inline; filename="Facture_{commande.numero}.pdf"'
        )
        return response
    except ImportError:
        # Fallback HTML si WeasyPrint non installé
        return HttpResponse(html)
