import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/features/produits/domain/models/product_model.dart';

class ProductDetailScreen extends StatefulWidget {
  final Product product;
  const ProductDetailScreen({super.key, required this.product});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  late Product _currentProduct;

  @override
  void initState() {
    super.initState();
    _currentProduct = widget.product;
  }

  @override
  Widget build(BuildContext context) {
    bool isAdmin = true; // Simulated for demonstration

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text("Détails Produit", style: GoogleFonts.outfit()),
        actions: [
          IconButton(
            onPressed: () => _showEditProductForm(),
            icon: const Icon(Icons.edit_outlined),
          ),
        ],
      ),
      body: SingleChildScrollView(
        child: Column(
          children: [
            _buildHeroHeader(),
            _buildQuickStats(),
            if (isAdmin) _buildFinancialSection(),
            _buildStockSection(),
            _buildPriceHistory(),
            const SizedBox(height: 100),
          ],
        ),
      ),
      bottomSheet: _buildActionButtons(context),
    );
  }

  void _showEditProductForm() {
    final nameCtrl = TextEditingController(text: _currentProduct.nom);
    final refCtrl = TextEditingController(text: _currentProduct.reference);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
          left: 20,
          right: 20,
          top: 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Modifier la Pièce",
              style: GoogleFonts.outfit(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            TextField(
              controller: nameCtrl,
              decoration: const InputDecoration(labelText: "Nom", filled: true),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: refCtrl,
              decoration: const InputDecoration(
                labelText: "Référence",
                filled: true,
              ),
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  setState(() {
                    _currentProduct = Product(
                      id: _currentProduct.id,
                      nom: nameCtrl.text,
                      reference: refCtrl.text,
                      prixVente: _currentProduct.prixVente,
                      quantite: _currentProduct.quantite,
                      seuilAlerte: _currentProduct.seuilAlerte,
                      codeBarre: _currentProduct.codeBarre,
                      estEnAlerte: _currentProduct.estEnAlerte,
                    );
                  });
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text("Modifications enregistrées"),
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                ),
                child: const Text(
                  "ENREGISTRER",
                  style: TextStyle(color: Colors.white),
                ),
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildHeroHeader() {
    return Container(
      width: double.infinity,
      color: Colors.white,
      padding: const EdgeInsets.all(24),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppTheme.backgroundColor,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.settings_suggest,
              size: 60,
              color: AppTheme.primaryColor,
            ),
          ),
          const SizedBox(height: 16),
          Text(
            _currentProduct.nom,
            textAlign: TextAlign.center,
            style: GoogleFonts.outfit(
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          Text(
            "Réf: ${_currentProduct.reference} • ${_currentProduct.marqueNom ?? 'Générique'}",
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 8),
          _buildBarcodeBadge(),
        ],
      ),
    );
  }

  Widget _buildBarcodeBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: Colors.blue[50],
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: Colors.blue[200]!),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.tag, size: 16, color: Colors.blue),
          const SizedBox(width: 8),
          Text(
            _currentProduct.codeBarre,
            style: const TextStyle(
              color: Colors.blue,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickStats() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          _buildStatBox(
            "PV Unitaire",
            "${_currentProduct.prixVente.toStringAsFixed(0)} GNF",
            AppTheme.primaryColor,
          ),
          const SizedBox(width: 16),
          _buildStatBox(
            "Catégorie",
            _currentProduct.categorieNom ?? "N/A",
            Colors.blueGrey,
          ),
        ],
      ),
    );
  }

  Widget _buildStatBox(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
        ),
        child: Column(
          children: [
            Text(
              label,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            const SizedBox(height: 4),
            Text(
              value,
              style: GoogleFonts.outfit(
                fontWeight: FontWeight.bold,
                fontSize: 16,
                color: color,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFinancialSection() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.green[900],
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                "ANALYSE FINANCIÈRE",
                style: TextStyle(
                  color: Colors.white70,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Row(
                children: [
                  const Icon(Icons.public, color: Colors.white70, size: 14),
                  const SizedBox(width: 4),
                  Text(
                    _currentProduct.achatDevise,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const Divider(color: Colors.white24, height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceAround,
            children: [
              _buildFinanceCol(
                "Achat (${_currentProduct.achatDevise})",
                _currentProduct.prixAchatDevise?.toStringAsFixed(2) ?? '0.00',
              ),
              _buildFinanceCol(
                "Taux (1 ${_currentProduct.achatDevise})",
                "${_currentProduct.tauxChangeAchat?.toStringAsFixed(0) ?? '1'} GNF",
              ),
              _buildFinanceCol(
                "Profit (GNF)",
                _currentProduct.benefice?.toStringAsFixed(0) ?? '0',
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            "Estimation de la marge : ${_currentProduct.tauxMarge?.toStringAsFixed(1) ?? '0'}%",
            style: const TextStyle(
              color: Colors.greenAccent,
              fontSize: 12,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFinanceCol(String label, String val) {
    return Column(
      children: [
        Text(
          label,
          style: const TextStyle(color: Colors.white60, fontSize: 10),
        ),
        Text(
          val,
          style: GoogleFonts.outfit(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 16,
          ),
        ),
      ],
    );
  }

  Widget _buildStockSection() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            "ÉTAT DU STOCK CONSOLIDÉ",
            style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Icon(
                Icons.inventory_2_outlined,
                color: _currentProduct.quantite > 0 ? Colors.green : Colors.red,
                size: 40,
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _currentProduct.formatStock(),
                      style: GoogleFonts.outfit(
                        fontWeight: FontWeight.bold,
                        fontSize: 18,
                      ),
                    ),
                    Text(
                      "Soit ${_currentProduct.quantite} ${_currentProduct.uniteSecondaire} au total",
                      style: const TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const Divider(height: 32),
          _buildLocationRow(
            "MAGASIN (Stock Gros)",
            "15 Cartons",
            Colors.blueGrey,
          ),
          const SizedBox(height: 12),
          _buildLocationRow(
            "BOUTIQUE (Détail)",
            "25 Pièces",
            AppTheme.primaryColor,
          ),
        ],
      ),
    );
  }

  Widget _buildLocationRow(String name, String qty, Color color) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          children: [
            Container(
              width: 8,
              height: 8,
              decoration: BoxDecoration(color: color, shape: BoxShape.circle),
            ),
            const SizedBox(width: 12),
            Text(
              name,
              style: const TextStyle(
                color: Colors.black87,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
        Text(
          qty,
          style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: color),
        ),
      ],
    );
  }

  Widget _buildPriceHistory() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Text(
              "HISTORIQUE DES PRIX",
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.grey),
            ),
          ),
          _buildHistoryItem(
            "03 Avril 2026",
            "450 000",
            "430 000",
            "Admin Djiba",
          ),
          _buildHistoryItem(
            "01 Janv 2026",
            "430 000",
            "400 000",
            "Admin Djiba",
          ),
        ],
      ),
    );
  }

  Widget _buildHistoryItem(
    String date,
    String nouveau,
    String ancien,
    String par,
  ) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          const Icon(Icons.history, color: Colors.grey, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(date, style: const TextStyle(fontWeight: FontWeight.bold)),
                Text(
                  "Par $par",
                  style: const TextStyle(fontSize: 10, color: Colors.grey),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                "$nouveau GNF",
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  color: Colors.green,
                ),
              ),
              Text(
                "au lieu de $ancien",
                style: const TextStyle(
                  fontSize: 10,
                  color: Colors.grey,
                  decoration: TextDecoration.lineThrough,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(color: Colors.black12, blurRadius: 10, spreadRadius: 1),
        ],
      ),
      child: ElevatedButton(
        onPressed: () {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text("Pièce ajoutée au panier de vente !"),
              behavior: SnackBarBehavior.floating,
            ),
          );
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.primaryColor,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          padding: const EdgeInsets.symmetric(vertical: 16),
        ),
        child: const Center(
          child: Text(
            "VENDRE MAINTENANT",
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
        ),
      ),
    );
  }
}
