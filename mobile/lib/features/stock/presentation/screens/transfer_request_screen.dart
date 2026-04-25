import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

class TransferRequestScreen extends StatefulWidget {
  const TransferRequestScreen({super.key});

  @override
  State<TransferRequestScreen> createState() => _TransferRequestScreenState();
}

class _TransferRequestScreenState extends State<TransferRequestScreen> {
  final List<Map<String, dynamic>> _cartItems = [];
  final String _selectedSource = "MAGASIN CENTRAL";
  final String _selectedDest = "BOUTIQUE HAMDALLAYE";

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text("Demande de Transfert", style: GoogleFonts.outfit(fontSize: 18)),
      ),
      body: Column(
        children: [
          _buildLocationHeader(),
          _buildItemPrompt(),
          Expanded(child: _buildItemList()),
          _buildSubmitSection(),
        ],
      ),
    );
  }

  Widget _buildLocationHeader() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        children: [
          _buildLocRow("DE", _selectedSource, Icons.warehouse_outlined, Colors.blueGrey),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 8),
            child: Icon(Icons.arrow_downward, color: Colors.grey, size: 16),
          ),
          _buildLocRow("VERS", _selectedDest, Icons.storefront_outlined, AppTheme.primaryColor),
        ],
      ),
    );
  }

  Widget _buildLocRow(String label, String value, IconData icon, Color color) {
    return Row(
      children: [
        SizedBox(width: 40, child: Text(label, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10, color: Colors.grey))),
        Icon(icon, size: 18, color: color),
        const SizedBox(width: 12),
        Text(value, style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: color)),
      ],
    );
  }

  Widget _buildItemPrompt() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: ElevatedButton.icon(
        onPressed: () => _showAddItemDialog(),
        icon: const Icon(Icons.add_shopping_cart, size: 18, color: Colors.white),
        label: const Text("Ajouter un article", style: TextStyle(color: Colors.white)),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.black87,
          minimumSize: const Size(double.infinity, 45),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      ),
    );
  }

  Widget _buildItemList() {
    if (_cartItems.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.local_shipping_outlined, size: 60, color: Colors.grey.withValues(alpha: 0.2)),
            const SizedBox(height: 16),
            const Text("Aucun article dans la demande", style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _cartItems.length,
      itemBuilder: (context, index) {
        final item = _cartItems[index];
        return Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(12)),
          child: Row(
            children: [
              const Icon(Icons.settings_suggest, color: AppTheme.primaryColor),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(item['nom'], style: const TextStyle(fontWeight: FontWeight.bold)),
                    Text("Réf: ${item['ref']}", style: const TextStyle(color: Colors.grey, fontSize: 10)),
                  ],
                ),
              ),
              Text("${item['qty']} CARTONS", style: GoogleFonts.outfit(fontWeight: FontWeight.bold, color: Colors.blueGrey)),
              IconButton(
                onPressed: () => setState(() => _cartItems.removeAt(index)),
                icon: const Icon(Icons.remove_circle_outline, color: Colors.redAccent, size: 20),
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildSubmitSection() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      child: SafeArea(
        child: ElevatedButton(
          onPressed: _cartItems.isEmpty ? null : () => _confirmTransfer(),
          style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primaryColor,
            minimumSize: const Size(double.infinity, 55),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          ),
          child: const Text("ENVOYER LA DEMANDE", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
        ),
      ),
    );
  }

  void _showAddItemDialog() {
    showDialog(
      context: context,
      builder: (context) {
        String qtyInput = "1";
        return AlertDialog(
          title: Text("Ajouter une Pièce", style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold)),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text("Sélectionnez la quantité en CARTONS", style: TextStyle(fontSize: 12, color: Colors.grey)),
              const SizedBox(height: 16),
              TextField(
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(labelText: "Nombre de Cartons", filled: true),
                onChanged: (val) => qtyInput = val,
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text("ANNULER")),
            ElevatedButton(
              onPressed: () {
                setState(() {
                  _cartItems.add({
                    'nom': "Plaquettes de frein Toyota",
                    'ref': "TOY-456-FB",
                    'qty': int.tryParse(qtyInput) ?? 1,
                  });
                });
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryColor),
              child: const Text("AJOUTER", style: TextStyle(color: Colors.white)),
            ),
          ],
        );
      }
    );
  }

  void _confirmTransfer() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text("Demande Envoyée"),
        content: const Text("Votre demande de transfert a été soumise au Magasin Central pour validation."),
        actions: [
          TextButton(onPressed: () { Navigator.pop(context); Navigator.pop(context); }, child: const Text("OK")),
        ],
      ),
    );
  }
}
