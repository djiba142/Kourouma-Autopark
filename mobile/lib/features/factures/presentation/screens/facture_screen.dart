import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/features/commandes/domain/models/commande_model.dart';

class FactureScreen extends StatelessWidget {
  final Commande commande;
  const FactureScreen({super.key, required this.commande});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      appBar: AppBar(
        title: Text("PIÈCE COMPTABLE", style: GoogleFonts.outfit(fontSize: 14, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: AppTheme.primaryColor,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            onPressed: () {
               ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text("📲 Partage de la facture BSG Business...")),
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            _buildInvoicePaper(context),
            const SizedBox(height: 30),
            _buildActionButtons(context),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildInvoicePaper(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.08),
            blurRadius: 24,
            offset: const Offset(0, 8),
          )
        ],
        border: Border.all(color: Colors.grey.withValues(alpha: 0.1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with Logo
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text("BSG AUTO-PIÈCES", style: GoogleFonts.outfit(fontSize: 22, fontWeight: FontWeight.w900, color: AppTheme.primaryColor)),
                  const Text("SNC - Capital 5.000.000 GNF", style: TextStyle(fontSize: 9, color: Colors.grey, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 4),
                  const Text("Sandervalia, Kaloum, Conakry", style: TextStyle(fontSize: 11, color: Colors.black87)),
                  const Text("Tél: +224 620 12 34 56", style: TextStyle(fontSize: 11, color: Colors.black87)),
                  const Text("Email: contact@bsgautoparts.gn", style: TextStyle(fontSize: 11, color: Colors.black87)),
                ],
              ),
              Image.asset('assets/images/bsg_logo.png', height: 75, width: 75),
            ],
          ),
          const SizedBox(height: 30),
          Container(height: 2, color: AppTheme.primaryColor.withValues(alpha: 0.1)),
          const SizedBox(height: 20),
          
          // Document Info
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("DESTINATAIRE :", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: Colors.grey, letterSpacing: 1.2)),
                  const SizedBox(height: 6),
                  Text(commande.clientDetails ?? "Client de passage", style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
                ],
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text("DOCUMENT :", style: TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: Colors.grey, letterSpacing: 1.2)),
                  const SizedBox(height: 4),
                  Text("FACTURE N° ${commande.numero}", style: const TextStyle(fontWeight: FontWeight.bold, color: AppTheme.primaryColor, fontSize: 14)),
                  Text("Date: ${commande.dateCreation.day}/${commande.dateCreation.month}/${commande.dateCreation.year}", style: const TextStyle(fontSize: 12)),
                ],
              ),
            ],
          ),
          const SizedBox(height: 30),
          
          // Table Header
          Container(
            padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
            decoration: BoxDecoration(
              color: AppTheme.primaryColor,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: const [
                Expanded(flex: 3, child: Text("DÉSIGNATION", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 10, letterSpacing: 1))),
                Expanded(child: Center(child: Text("QTÉ", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 10, letterSpacing: 1)))),
                Expanded(flex: 2, child: Center(child: Text("TOTAL GNF", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 10, letterSpacing: 1)))),
              ],
            ),
          ),
          
          // Itemized Lines
          const SizedBox(height: 8),
          ...commande.lignes.map((line) => _buildInvoiceRow(
            line.produitDetails?.nom ?? "Produit #${line.produitId}", 
            "${line.quantite}", 
            line.sousTotal.toInt().toString()
          )),
          
          const SizedBox(height: 20),
          Container(height: 1, color: Colors.grey.withValues(alpha: 0.2)),
          const SizedBox(height: 20),
          
          // Financial Summary
          Align(
            alignment: Alignment.centerRight,
            child: SizedBox(
              width: 240,
              child: Column(
                children: [
                   _buildSummaryRow("TOTAL BRUT H.T", "${commande.totalHt.toInt()}", false),
                   _buildSummaryRow("REMISE ACCORDÉE", "${commande.remise.toInt()}", false, isNegative: true),
                   const Padding(
                     padding: EdgeInsets.symmetric(vertical: 4.0),
                     child: Divider(thickness: 1, color: AppTheme.primaryColor),
                   ),
                   _buildSummaryRow("TOTAL NET T.T.C", "${commande.totalTtc.toInt()}", true, color: AppTheme.primaryColor, fontSize: 16),
                   const SizedBox(height: 12),
                   _buildSummaryRow("MONTANT RÉGLÉ", "${(commande.totalTtc - commande.resteAPayer).toInt()}", false, color: Colors.green),
                   if (commande.resteAPayer > 0)
                    _buildSummaryRow("SOLDE RESTANT DÛ", "${commande.resteAPayer.toInt()}", true, color: Colors.red),
                ],
              ),
            ),
          ),
          
          const SizedBox(height: 60),
          // Signatures Area
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildSignatureBlock("Le Client"),
              _buildSignatureBlock("La Direction BSG"),
            ],
          ),
          
          const SizedBox(height: 40),
          Center(
            child: Column(
              children: [
                const Icon(Icons.verified_user_outlined, color: Colors.green, size: 30),
                const SizedBox(height: 8),
                Text(
                  "Merci de votre confiance. Facture certifiée conforme.",
                  style: GoogleFonts.outfit(fontSize: 10, color: Colors.grey, fontWeight: FontWeight.bold),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInvoiceRow(String name, String qty, String total) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.withValues(alpha: 0.05))),
      ),
      child: Row(
        children: [
          Expanded(flex: 3, child: Text(name, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500))),
          Expanded(child: Center(child: Text(qty, style: const TextStyle(fontSize: 12)))),
          Expanded(flex: 2, child: Center(child: Text("$total GNF", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)))),
        ],
      ),
    );
  }

  Widget _buildSummaryRow(String label, String value, bool bold, {Color? color, double fontSize = 12, bool isNegative = false}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontWeight: bold ? FontWeight.bold : FontWeight.w500, fontSize: bold ? fontSize - 2 : fontSize - 1)),
          Text("${isNegative ? '-' : ''}$value GNF", style: TextStyle(fontWeight: bold ? FontWeight.bold : FontWeight.bold, color: color, fontSize: fontSize)),
        ],
      ),
    );
  }

  Widget _buildSignatureBlock(String title) {
    return Column(
      children: [
        Text(title, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, decoration: TextDecoration.underline)),
        const SizedBox(height: 40),
        Container(width: 80, height: 1, color: Colors.grey[300]),
      ],
    );
  }

  Widget _buildActionButtons(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: Column(
        children: [
          ElevatedButton.icon(
            onPressed: () {
               ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text("🖨️ Connexion à l'imprimante BSG en cours..."),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            icon: const Icon(Icons.print_rounded, color: Colors.white),
            label: const Text("IMPRIMER LA FACTURE", style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryColor,
              minimumSize: const Size(double.infinity, 60),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              elevation: 4,
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            onPressed: () {
               ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text("💾 Facture enregistrée dans les documents."),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            icon: const Icon(Icons.download_rounded),
            label: const Text("TÉLÉCHARGER LE PDF", style: TextStyle(fontWeight: FontWeight.bold)),
            style: OutlinedButton.styleFrom(
              minimumSize: const Size(double.infinity, 60),
              side: const BorderSide(color: AppTheme.primaryColor, width: 2),
              foregroundColor: AppTheme.primaryColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
            ),
          ),
        ],
      ),
    );
  }
}
