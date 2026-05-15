"""
web/views_clients.py
Gestion de la base clients et fournisseurs.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from web.middleware import employe_or_admin, admin_required
from clients.models import Client
from achats.models import Fournisseur


@employe_or_admin
def clients_liste(request):
    return render(request, 'web/clients/liste.html', {
        'title': 'Clients',
        'clients': Client.objects.filter(actif=True).order_by('nom')
    })


@employe_or_admin
def client_detail(request, pk):
    import urllib.parse
    client = get_object_or_404(Client, pk=pk)
    
    wa_phone = str(client.telephone).replace(' ', '').replace('+', '') if client.telephone else ''
    msg = f"Bonjour {client.nom}, sauf erreur de notre part, votre compte présente un solde débiteur de {client.total_dette:,.0f} GNF. Merci de nous contacter pour régulariser cette situation. Cordialement, AutoPiecesPro."
    msg = msg.replace(',', ' ')
    wa_text = urllib.parse.quote(msg) if client.total_dette > 0 else ""

    return render(request, 'web/clients/detail.html', {
        'title': client.nom,
        'client': client,
        'commandes': client.commandes.order_by('-date_creation')[:10],
        'wa_phone': wa_phone,
        'wa_text': wa_text
    })


@employe_or_admin
def client_nouveau(request):
    if request.method == 'POST':
        Client.objects.create(
            nom=request.POST.get('nom'),
            telephone=request.POST.get('telephone'),
            email=request.POST.get('email'),
            adresse=request.POST.get('adresse'),
            limite_credit=request.POST.get('limite_credit', 0)
        )
        messages.success(request, "Client créé.")
        return redirect('web:clients_liste')
    return render(request, 'web/clients/form.html', {'title': 'Nouveau Client'})


@admin_required
def fournisseurs_liste(request):
    return render(request, 'web/clients/fournisseurs.html', {
        'title': 'Fournisseurs',
        'fournisseurs': Fournisseur.objects.all()
    })

@admin_required
def fournisseur_detail(request, pk):
    fournisseur = get_object_or_404(Fournisseur, pk=pk)
    achats = fournisseur.achats.order_by('-date_commande')
    
    return render(request, 'web/clients/fournisseur_detail.html', {
        'title': f"Fournisseur : {fournisseur.nom}",
        'fournisseur': fournisseur,
        'achats': achats
    })


@admin_required
def rapport_dettes(request):
    # Get all active clients with a debt > 0
    clients_actifs = Client.objects.filter(actif=True)
    dettes_list = []
    
    import urllib.parse
    for c in clients_actifs:
        dette = c.total_dette
        if dette > 0:
            msg = f"Bonjour {c.nom}, sauf erreur de notre part, votre compte présente un solde débiteur de {dette:,.0f} GNF. Merci de nous contacter pour régulariser cette situation. Cordialement, AutoPiecesPro."
            msg = msg.replace(',', ' ') # format number cleanly
            
            # Clean phone number (remove spaces, +, etc)
            phone = str(c.telephone).replace(' ', '').replace('+', '') if c.telephone else ''
            
            dettes_list.append({
                'client': c,
                'dette': float(dette),
                'limite': float(c.limite_credit),
                'depassement': dette > c.limite_credit,
                'wa_phone': phone,
                'wa_text': urllib.parse.quote(msg)
            })
            total_general += dette

    # Sort by debt descending
    dettes_list.sort(key=lambda x: x['dette'], reverse=True)

    export = request.GET.get('export')
    
    if export == 'excel':
        import openpyxl
        from django.http import HttpResponse
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Dettes Clients"
        
        headers = ["Nom Client", "Téléphone", "Dette (GNF)", "Limite Crédit (GNF)", "Statut Alerte"]
        ws.append(headers)
        
        for d in dettes_list:
            ws.append([
                d['client'].nom,
                d['client'].telephone,
                d['dette'],
                d['limite'],
                "Dépassement" if d['depassement'] else "OK"
            ])
            
        from web.excel_utils import add_logo_to_sheet
        add_logo_to_sheet(ws, "Rapport des Dettes Clients")
        
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="BANGALY_Dettes_Clients.xlsx"'
        wb.save(response)
        return response

    if export == 'pdf':
        import weasyprint
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        
        html_string = render_to_string('web/clients/rapport_dettes_pdf.html', {
            'dettes_list': dettes_list,
            'total_general': total_general,
        })
        pdf_file = weasyprint.HTML(string=html_string).write_pdf()
        
        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Rapport_Dettes_Clients.pdf"'
        return response

    return render(request, 'web/clients/rapport_dettes.html', {
        'title': 'Rapport Dettes Clients',
        'dettes_list': dettes_list,
        'total_general': total_general,
    })
