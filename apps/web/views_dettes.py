"""
web/views_dettes.py
═════════════════════════════════════════════════════════════════════
Rapport Dettes Clients — Admin + Employé

  1. rapport_dettes()     — tableau classé par dette décroissante
                            avec alertes, score, historique rapide
  2. export_dettes_excel()— export openpyxl 2 onglets
                            (Résumé dettes + Détail commandes impayées)
  3. client_whatsapp()    — redirige vers WhatsApp avec message
                            pré-rempli (relance dette)
═════════════════════════════════════════════════════════════════════
"""
import logging
from django.shortcuts import redirect, get_object_or_404, render
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone

from web.middleware import employe_or_admin, admin_required
from clients.models import Client
from commandes.models import Commande, Paiement

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helper — enrichit chaque client avec ses données de dette calculées en DB
# (évite N+1 en utilisant annotate + propriétés model)
# ─────────────────────────────────────────────────────────────────────────────

def _build_dettes(filtre: str = 'tous'):
    """
    Retourne une liste de dicts triée par dette décroissante.
    filtre : 'tous' | 'alerte' | 'bloque' | 'bon'
    """
    clients = Client.objects.filter(actif=True).prefetch_related(
        'commandes', 'commandes__paiements'
    )

    rows = []
    for c in clients:
        dette      = float(c.total_dette)
        total_ach  = float(c.total_achats)
        total_paye = float(c.total_paye)
        limite     = float(c.limite_credit)
        alerte     = c.alerte_credit

        # Nombre de commandes impayées
        nb_impayes = c.commandes.filter(
            statut_paiement__in=['NON_PAYE', 'PARTIEL'],
            statut__in=['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE']
        ).count()

        # Pourcentage limite utilisée
        pct_limite = 0
        if limite > 0:
            pct_limite = min(int(dette / limite * 100), 100)

        row = {
            'client':      c,
            'dette':       dette,
            'total_ach':   total_ach,
            'total_paye':  total_paye,
            'limite':      limite,
            'alerte':      alerte,
            'nb_impayes':  nb_impayes,
            'pct_limite':  pct_limite,
            'score':       c.score_statut,
        }

        # Application du filtre
        if filtre == 'alerte' and not alerte:
            continue
        if filtre == 'bloque' and c.score_statut != 'BLOQUE':
            continue
        if filtre == 'bon' and c.score_statut not in ('BON', 'MOYEN'):
            continue
        if dette <= 0 and filtre not in ('tous', 'bon'):
            continue

        rows.append(row)

    # Tri : dette décroissante, puis nom
    rows.sort(key=lambda r: (-r['dette'], r['client'].nom))
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 1 — RAPPORT DETTES
# ─────────────────────────────────────────────────────────────────────────────

@employe_or_admin
def rapport_dettes(request):
    filtre = request.GET.get('filtre', 'tous')
    if filtre not in ('tous', 'alerte', 'bloque', 'bon'):
        filtre = 'tous'

    rows = _build_dettes(filtre)

    # KPIs globaux (tous clients confondus, sans filtre)
    tous = _build_dettes('tous')
    total_dettes    = sum(r['dette'] for r in tous)
    nb_en_alerte    = sum(1 for r in tous if r['alerte'])
    nb_bloques      = sum(1 for r in tous if r['score'] == 'BLOQUE')
    nb_avec_dette   = sum(1 for r in tous if r['dette'] > 0)
    total_clients   = len(tous)

    # Commandes impayées toutes boutiques
    nb_cmd_impayes = Commande.objects.filter(
        statut_paiement__in=['NON_PAYE', 'PARTIEL'],
        statut__in=['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE']
    ).count()

    # Données pour Chart.js (JSON safe)
    import json
    top_10 = rows[:10]
    labels_json  = json.dumps([r['client'].nom[:16] for r in top_10])
    dettes_json  = json.dumps([r['dette'] for r in top_10])
    limites_json = json.dumps([r['limite'] for r in top_10])

    return render(request, 'web/clients/rapport_dettes.html', {
        'title':          'Rapport Dettes Clients',
        'rows':           rows,
        'filtre':         filtre,
        'total_dettes':   total_dettes,
        'nb_en_alerte':   nb_en_alerte,
        'nb_bloques':     nb_bloques,
        'nb_avec_dette':  nb_avec_dette,
        'total_clients':  total_clients,
        'nb_cmd_impayes': nb_cmd_impayes,
        'labels_json':    labels_json,
        'dettes_json':    dettes_json,
        'limites_json':   limites_json,
        'is_admin':       request.user.role == 'ADMIN',
    })


# ─────────────────────────────────────────────────────────────────────────────
# 2 — DÉTAIL COMMANDES IMPAYÉES D'UN CLIENT
# ─────────────────────────────────────────────────────────────────────────────

@employe_or_admin
def client_impayes(request, pk):
    client = get_object_or_404(Client, pk=pk)
    commandes_impayes = Commande.objects.filter(
        client=client,
        statut_paiement__in=['NON_PAYE', 'PARTIEL'],
        statut__in=['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE']
    ).prefetch_related('paiements').order_by('-date_creation')

    lignes = []
    for cmd in commandes_impayes:
        total_paye = sum(float(p.montant) for p in cmd.paiements.all())
        reste = float(cmd.total_ttc) - total_paye
        lignes.append({
            'cmd':       cmd,
            'paye':      total_paye,
            'reste':     reste,
        })

    return render(request, 'web/clients/impayes_detail.html', {
        'title':   f'Impayés — {client.nom}',
        'client':  client,
        'lignes':  lignes,
        'dette_totale': float(client.total_dette),
    })


# ─────────────────────────────────────────────────────────────────────────────
# 3 — EXPORT EXCEL
# ─────────────────────────────────────────────────────────────────────────────

@employe_or_admin
def export_dettes_excel(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    rows = _build_dettes('tous')

    wb  = openpyxl.Workbook()

    # ── Onglet 1 : Résumé dettes ─────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = 'Résumé Dettes'

    hfill = PatternFill('solid', fgColor='1A3A5C')
    hfont = Font(bold=True, color='FFFFFF', size=11)
    ctr   = Alignment(horizontal='center', vertical='center')
    rfont = Font(bold=True, color='C0392B')
    gfont = Font(bold=True, color='1E7E34')
    ofont = Font(bold=True, color='E67E22')

    headers1 = ['Client', 'Téléphone', 'Total Achats', 'Total Payé',
                'DETTE GNF', 'Limite Crédit', '% Limite', 'Score', 'Cmd Impayées']
    widths1  = [28, 18, 18, 18, 18, 18, 12, 14, 14]

    for c, (h, w) in enumerate(zip(headers1, widths1), 1):
        cell = ws1.cell(1, c, h)
        cell.font = hfont; cell.fill = hfill; cell.alignment = ctr
        ws1.column_dimensions[get_column_letter(c)].width = w
    ws1.row_dimensions[1].height = 22

    for r, row in enumerate(rows, 2):
        ws1.cell(r, 1, row['client'].nom)
        ws1.cell(r, 2, row['client'].telephone)
        ws1.cell(r, 3, row['total_ach']).number_format = '#,##0'
        ws1.cell(r, 4, row['total_paye']).number_format = '#,##0'

        dette_cell = ws1.cell(r, 5, row['dette'])
        dette_cell.number_format = '#,##0'
        if row['dette'] <= 0:
            dette_cell.font = gfont
        elif row['alerte']:
            dette_cell.font = rfont
        else:
            dette_cell.font = ofont

        ws1.cell(r, 6, row['limite']).number_format = '#,##0'

        pct_cell = ws1.cell(r, 7, f"{row['pct_limite']}%")
        if row['pct_limite'] >= 100:
            pct_cell.font = rfont
        elif row['pct_limite'] >= 80:
            pct_cell.font = ofont

        score_cell = ws1.cell(r, 8, row['score'])
        score_cell.font = Font(
            bold=True,
            color={
                'BON': '1E7E34', 'MOYEN': 'E67E22',
                'MAUVAIS': 'C0392B', 'BLOQUE': '7B241C'
            }.get(row['score'], '000000')
        )
        ws1.cell(r, 9, row['nb_impayes'])

    # Ligne totaux
    total_row = len(rows) + 2
    ws1.cell(total_row, 1, 'TOTAL').font = Font(bold=True, size=12)
    t = ws1.cell(total_row, 5, sum(r['dette'] for r in rows))
    t.number_format = '#,##0'
    t.font = Font(bold=True, size=12, color='C0392B')

    # ── Onglet 2 : Commandes impayées ────────────────────────────────────────
    ws2 = wb.create_sheet('Commandes Impayées')
    headers2 = ['Client', 'Téléphone', 'N° Commande', 'Total TTC',
                'Total Payé', 'RESTE DÛ', 'Statut', 'Date']
    widths2  = [25, 16, 22, 16, 16, 16, 16, 16]

    for c, (h, w) in enumerate(zip(headers2, widths2), 1):
        cell = ws2.cell(1, c, h)
        cell.font = hfont; cell.fill = hfill; cell.alignment = ctr
        ws2.column_dimensions[get_column_letter(c)].width = w

    r = 2
    for row in rows:
        if row['nb_impayes'] == 0:
            continue
        cmds = Commande.objects.filter(
            client=row['client'],
            statut_paiement__in=['NON_PAYE', 'PARTIEL'],
            statut__in=['VALIDEE', 'EN_PREPARATION', 'EXPEDIEE', 'LIVREE']
        ).prefetch_related('paiements')

        for cmd in cmds:
            paye  = sum(float(p.montant) for p in cmd.paiements.all())
            reste = float(cmd.total_ttc) - paye

            ws2.cell(r, 1, row['client'].nom)
            ws2.cell(r, 2, row['client'].telephone)
            ws2.cell(r, 3, cmd.numero)
            ws2.cell(r, 4, float(cmd.total_ttc)).number_format = '#,##0'
            ws2.cell(r, 5, paye).number_format = '#,##0'
            reste_cell = ws2.cell(r, 6, reste)
            reste_cell.number_format = '#,##0'
            reste_cell.font = rfont
            ws2.cell(r, 7, cmd.get_statut_display())
            ws2.cell(r, 8, cmd.date_creation.strftime('%d/%m/%Y'))
            r += 1

    from web.excel_utils import add_logo_to_sheet
    add_logo_to_sheet(ws1, "Résumé des Dettes")
    add_logo_to_sheet(ws2, "Détail par Client")

    # En-tête du fichier
    now  = timezone.now().strftime('%Y%m%d_%H%M')
    resp = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    resp['Content-Disposition'] = f'attachment; filename="BANGALY_Dettes_{now}.xlsx"'
    wb.save(resp)
    return resp


# ─────────────────────────────────────────────────────────────────────────────
# 4 — RELANCE WHATSAPP
# ─────────────────────────────────────────────────────────────────────────────

@employe_or_admin
def client_whatsapp(request, pk):
    """
    Construit un lien WhatsApp avec message pré-rempli de relance dette.
    Redirige directement vers wa.me — aucune donnée n'est stockée.
    """
    client = get_object_or_404(Client, pk=pk)
    dette  = float(client.total_dette)

    tel = ''.join(c for c in client.telephone if c.isdigit() or c == '+')
    if not tel.startswith('+'):
        tel = '+224' + tel.lstrip('0')

    if dette > 0:
        msg = (
            f"Bonjour {client.nom},\n\n"
            f"Nous vous rappelons que vous avez un solde impayé de "
            f"{dette:,.0f} GNF auprès de BSG.\n\n"
            f"Merci de régulariser votre situation dans les plus brefs délais.\n\n"
            f"Cordialement,\nL'équipe BSG"
        )
    else:
        msg = (
            f"Bonjour {client.nom},\n\n"
            f"Merci pour votre confiance. "
            f"N'hésitez pas à nous contacter pour toute commande.\n\n"
            f"L'équipe BSG"
        )

    import urllib.parse
    url = f"https://wa.me/{tel}?text={urllib.parse.quote(msg)}"
    return redirect(url)
