import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

class PurchaseOrderScreen extends StatefulWidget {
  const PurchaseOrderScreen({super.key});

  @override
  State<PurchaseOrderScreen> createState() => _PurchaseOrderScreenState();
}

class _PurchaseOrderScreenState extends State<PurchaseOrderScreen> {
  final List<Map<String, dynamic>> _items = [];
  double _exchangeRate = 8500.0;
  String _selectedCurrency = 'USD';
  
  final _rateController = TextEditingController(text: "8500");

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text("Bon de Commande", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          _buildProcurementHeader(),
          Expanded(
            child: _items.isEmpty 
              ? _buildEmptyState()
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _items.length,
                  itemBuilder: (context, index) => _buildOrderItem(index),
                ),
          ),
          _buildSummaryArea(),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _addItem(),
        backgroundColor: AppTheme.primaryColor,
        icon: const Icon(Icons.add_shopping_cart, color: Colors.white),
        label: const Text("Ajouter une Pièce", style: TextStyle(color: Colors.white)),
      ),
    );
  }

  Widget _buildProcurementHeader() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppTheme.surfaceColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Column(
        children: [
          Row(
            children: [
               const Icon(Icons.business, color: Colors.white70),
               const SizedBox(width: 12),
               Text("FOURNISSEUR: China Parts Ltd", style: GoogleFonts.outfit(color: Colors.white, fontWeight: FontWeight.bold)),
            ],
          ),
          const Divider(height: 30, color: Colors.white10),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("DEVISE D'ACHAT", style: TextStyle(color: Colors.white60, fontSize: 10)),
                    DropdownButton<String>(
                      value: _selectedCurrency,
                      dropdownColor: AppTheme.surfaceColor,
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      underline: Container(),
                      items: ['USD', 'EUR', 'GNF'].map((String value) {
                        return DropdownMenuItem<String>(value: value, child: Text(value));
                      }).toList(),
                      onChanged: (val) => setState(() => _selectedCurrency = val!),
                    ),
                  ],
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("TAUX DE CHANGE", style: TextStyle(color: Colors.white60, fontSize: 10)),
                    TextField(
                      controller: _rateController,
                      keyboardType: TextInputType.number,
                      style: const TextStyle(color: AppTheme.primaryColor, fontWeight: FontWeight.bold),
                      decoration: const InputDecoration(suffixText: "GNF", contentPadding: EdgeInsets.zero, border: InputBorder.none),
                      onChanged: (val) => setState(() => _exchangeRate = double.tryParse(val) ?? 1.0),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.assignment_outlined, size: 80, color: Colors.grey[300]),
          const SizedBox(height: 16),
          Text("Aucune pièce ajoutée", style: TextStyle(color: Colors.grey[600], fontSize: 16)),
          Text("Appuyez sur + pour commencer", style: TextStyle(color: Colors.grey[400], fontSize: 12)),
        ],
      ),
    );
  }

  Widget _buildOrderItem(int index) {
    final item = _items[index];
    final gnfPrice = item['price'] * _exchangeRate;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(item['name'], style: const TextStyle(fontWeight: FontWeight.bold)),
                Text("Ref: ${item['ref']}", style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text("${item['qty']} Cartons x ${item['price']} $_selectedCurrency", style: const TextStyle(fontWeight: FontWeight.bold)),
              Text("≃ ${gnfPrice.toInt()} GNF / Unité", style: const TextStyle(color: Colors.green, fontSize: 10, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSummaryArea() {
    double totalDevise = _items.fold(0, (sum, item) => sum + (item['qty'] * item['price']));
    double totalGnf = totalDevise * _exchangeRate;

    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(30)),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 20)],
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("TOTAL DEVISE", style: TextStyle(fontWeight: FontWeight.bold)),
              Text("${totalDevise.toStringAsFixed(2)} $_selectedCurrency", style: GoogleFonts.outfit(color: AppTheme.primaryColor, fontWeight: FontWeight.bold, fontSize: 18)),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("CONTRE-VALEUR GNF", style: TextStyle(color: Colors.grey, fontSize: 14)),
              Text("${totalGnf.toInt()} GNF", style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 20)),
            ],
          ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: _items.isEmpty ? null : () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Bon de commande enregistré !")),
                );
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryColor, padding: const EdgeInsets.symmetric(vertical: 18)),
              child: const Text("VALIDER LA COMMANDE", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }

  void _addItem() {
    final nameCtrl = TextEditingController();
    final refCtrl = TextEditingController();
    final qtyCtrl = TextEditingController();
    final priceCtrl = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Ajouter une Pièce", style: GoogleFonts.outfit()),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: "Nom du produit")),
              const SizedBox(height: 12),
              TextField(controller: refCtrl, decoration: const InputDecoration(labelText: "Référence")),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(child: TextField(controller: qtyCtrl, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: "Quantité (Cartons)"))),
                  const SizedBox(width: 12),
                  Expanded(child: TextField(controller: priceCtrl, keyboardType: TextInputType.number, decoration: InputDecoration(labelText: "Prix ($_selectedCurrency)"))),
                ],
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("ANNULER")),
          ElevatedButton(
            onPressed: () {
              if (nameCtrl.text.isNotEmpty && qtyCtrl.text.isNotEmpty && priceCtrl.text.isNotEmpty) {
                setState(() {
                  _items.add({
                    'name': nameCtrl.text,
                    'ref': refCtrl.text.isNotEmpty ? refCtrl.text : 'N/A',
                    'qty': int.tryParse(qtyCtrl.text) ?? 1,
                    'price': double.tryParse(priceCtrl.text) ?? 0.0,
                  });
                });
                Navigator.pop(context);
              }
            }, 
            child: const Text("AJOUTER")
          ),
        ],
      ),
    );
  }
}
