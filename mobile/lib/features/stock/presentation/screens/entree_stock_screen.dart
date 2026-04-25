import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/shared/models/produit.dart';

class EntreeStockScreen extends StatefulWidget {
  const EntreeStockScreen({super.key});

  @override
  State<EntreeStockScreen> createState() => _EntreeStockScreenState();
}

class _EntreeStockScreenState extends State<EntreeStockScreen> {
  Produit? _selectedProduit;
  final _qtyController = TextEditingController();
  final _priceController = TextEditingController();
  final _supplierController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(title: const Text("Réapprovisionnement")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildProductSelector(),
            if (_selectedProduit != null) ...[
              const SizedBox(height: 32),
              _buildProductSummary(),
              const SizedBox(height: 32),
              _buildEntryForm(),
              const SizedBox(height: 30),
              _buildStockPreview(),
              const SizedBox(height: 40),
            ],
            if (_selectedProduit != null)
              ElevatedButton(
                onPressed: () {
                  // Submit stock inflow
                },
                child: const Text("VAlIDER L'ENTRÉE"),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildProductSelector() {
    return Material(
      borderRadius: BorderRadius.circular(20),
      elevation: 4,
      shadowColor: Colors.black12,
      child: TextField(
        decoration: InputDecoration(
          hintText: "Chercher un produit...",
          prefixIcon: const Icon(Icons.search, color: AppTheme.primaryColor),
          filled: true,
          fillColor: Colors.white,
        ),
      ),
    );
  }

  Widget _buildProductSummary() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.1)),
      ),
      child: Row(
        children: [
          const Icon(Icons.inventory_2, color: AppTheme.primaryColor),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _selectedProduit?.nom ?? "Produit sélectionné",
                  style: GoogleFonts.outfit(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                  ),
                ),
                Text(
                  "Réf: ${_selectedProduit?.reference}",
                  style: const TextStyle(color: Colors.grey),
                ),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                "${_selectedProduit?.quantite}",
                style: GoogleFonts.outfit(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryColor,
                ),
              ),
              const Text(
                "En stock",
                style: TextStyle(fontSize: 10, color: Colors.grey),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEntryForm() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildLabel("Informations de livraison"),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: _buildField(
                "Quantité reçue",
                "Ex: 50",
                _qtyController,
                suffix: "Unités",
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: _buildField("Nouv. Prix Achat", "GNF", _priceController),
            ),
          ],
        ),
        const SizedBox(height: 20),
        _buildField(
          "Fournisseur / N° Bon",
          "Nom du fournisseur",
          _supplierController,
        ),
      ],
    );
  }

  Widget _buildField(
    String label,
    String hint,
    TextEditingController ctrl, {
    String? suffix,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: Colors.grey,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: ctrl,
          decoration: InputDecoration(
            hintText: hint,
            suffixText: suffix,
            fillColor: Colors.white,
          ),
          onChanged: (_) => setState(() {}),
        ),
      ],
    );
  }

  Widget _buildStockPreview() {
    int received = int.tryParse(_qtyController.text) ?? 0;
    int current = _selectedProduit?.quantite ?? 0;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildStockMini("Actuel", current.toString(), Colors.grey),
          const Icon(Icons.arrow_forward, color: Colors.grey),
          _buildStockMini(
            "Previsionnel",
            (current + received).toString(),
            AppTheme.successColor,
          ),
        ],
      ),
    );
  }

  Widget _buildStockMini(String label, String value, Color color) {
    return Column(
      children: [
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
        const SizedBox(height: 4),
        Text(
          value,
          style: GoogleFonts.outfit(
            fontSize: 24,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildLabel(String text) {
    return Text(
      text,
      style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold),
    );
  }
}
