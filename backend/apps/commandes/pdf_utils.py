"""
Utilitaires pour génération de factures PDF
Utilise ReportLab (plus léger que WeasyPrint)
"""
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from .models import Commande


def generer_facture_pdf(commande: Commande) -> BytesIO:
    """
    Génère une facture PDF pour une commande
    Retourne un objet BytesIO contenant le PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20, bottomMargin=20)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a237e'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#424242'),
        spaceAfter=6,
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=9,
    )
    
    # Elements du document
    elements = []
    
    # ── EN-TÊTE ──
    elements.append(Paragraph("FACTURE", title_style))
    elements.append(Spacer(1, 0.2 * inch))
    
    # Infos facture
    info_data = [
        [f"N° Facture: <b>{commande.numero}</b>", f"Date: <b>{datetime.now().strftime('%d/%m/%Y')}</b>"],
        [f"Type: <b>{commande.get_type_vente_display()}</b>", f"Statut: <b>{commande.get_statut_display()}</b>"],
    ]
    
    info_table = Table(info_data, colWidths=[3.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # ── CLIENT ──
    if commande.client:
        elements.append(Paragraph("CLIENT", heading_style))
        client_data = [
            [f"<b>{commande.client.nom}</b>"],
            [f"Email: {commande.client.email}"],
            [f"Téléphone: {commande.client.telephone}"],
            [f"Adresse: {commande.client.adresse}"],
        ]
        client_table = Table(client_data, colWidths=[7 * inch])
        client_table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 9),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(client_table)
        elements.append(Spacer(1, 0.2 * inch))
    
    # ── LIGNES DE COMMANDE ──
    elements.append(Paragraph("ARTICLES", heading_style))
    
    lignes_data = [
        ['Produit', 'Référence', 'Qté', 'P.U (GNF)', 'Total (GNF)']
    ]
    
    for ligne in commande.lignes.all():
        lignes_data.append([
            ligne.produit.nom[:30],
            ligne.produit.reference,
            str(ligne.quantite),
            f"{float(ligne.prix_unitaire):,.0f}",
            f"{float(ligne.sous_total):,.0f}",
        ])
    
    lignes_table = Table(lignes_data, colWidths=[2.5 * inch, 1.2 * inch, 0.8 * inch, 1.2 * inch, 1.2 * inch])
    lignes_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#424242')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONT', (0, 1), (-1, -1), 'Helvetica', 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(lignes_table)
    elements.append(Spacer(1, 0.2 * inch))
    
    # ── TOTAUX ──
    totaux_data = [
        ['Total HT (GNF):', f"{float(commande.total_ht):,.2f}"],
        [f"Remise ({commande.get_type_remise_display()}):", f"-{float(commande.remise):,.2f}"],
        ['TOTAL TTC (GNF):', f"<b>{float(commande.total_ttc):,.2f}</b>"],
    ]
    
    if commande.paiements.exists():
        total_paye = sum(float(p.montant) for p in commande.paiements.all())
        totaux_data.append(['Montant Payé (GNF):', f"<b>{total_paye:,.2f}</b>"])
        totaux_data.append(['Reste à Payer (GNF):', f"<b>{float(commande.reste_a_payer):,.2f}</b>"])
    
    totaux_table = Table(totaux_data, colWidths=[5 * inch, 2 * inch])
    totaux_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, -3), (-1, -1), colors.HexColor('#e3f2fd')),
        ('LINEABOVE', (0, -3), (-1, -3), 2, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(totaux_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    # ── PAIEMENTS ──
    if commande.paiements.exists():
        elements.append(Paragraph("PAIEMENTS ENREGISTRÉS", heading_style))
        
        paiements_data = [['Date', 'Montant (GNF)', 'Mode', 'Référence']]
        for paiement in commande.paiements.all():
            paiements_data.append([
                paiement.date_paiement.strftime('%d/%m/%Y %H:%M'),
                f"{float(paiement.montant):,.2f}",
                paiement.get_mode_paiement_display(),
                paiement.reference_transaction or '-',
            ])
        
        paiements_table = Table(paiements_data, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 2 * inch])
        paiements_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#424242')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('PADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(paiements_table)
    
    # ── PIED DE PAGE ──
    elements.append(Spacer(1, 0.3 * inch))
    elements.append(Paragraph(
        f"<i>Facture générée le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer
