import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

class ReceptionScreen extends StatefulWidget {
  final String orderReference;
  final String vendorName;
  const ReceptionScreen({
    super.key, 
    required this.orderReference,
    required this.vendorName,
  });

  @override
  State<ReceptionScreen> createState() => _ReceptionScreenState();
}

class _ReceptionScreenState extends State<ReceptionScreen> {
  final List<Map<String, dynamic>> _expectedItems = [
    {'name': 'Plaquettes de Frein TY-44560', 'expected_qty': 10, 'received_qty': 0},
    {'name': 'Filtre à Huile FH-102', 'expected_qty': 25, 'received_qty': 0},
    {'name': 'Courroie Distribution CD-99', 'expected_qty': 5, 'received_qty': 0},
  ];

  @override
  Widget build(BuildContext context) {
    bool allReceived = _expectedItems.every((item) => item['received_qty'] == item['expected_qty']);

    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text("Réception Marchandise", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
      ),
      body: Column(
        children: [
          _buildReceptionHeader(),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: _expectedItems.length,
              itemBuilder: (context, index) => _buildReceptionItem(index),
            ),
          ),
          _buildActionArea(allReceived),
        ],
      ),
    );
  }

  Widget _buildReceptionHeader() {
    return Container(
      margin: const EdgeInsets.all(16),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.inventory_rounded, color: AppTheme.primaryColor),
              const SizedBox(width: 12),
              Text("Bon de Commande : ${widget.orderReference}", 
                style: GoogleFonts.outfit(color: Colors.black87, fontWeight: FontWeight.bold, fontSize: 16)),
            ],
          ),
          const SizedBox(height: 8),
          Text("Fournisseur : ${widget.vendorName}", style: const TextStyle(color: Colors.black54)),
          const Divider(height: 30, color: Colors.black12),
          Row(
            children: [
              const Icon(Icons.warning_amber_rounded, color: AppTheme.warningColor, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  "Vérifiez physiquement chaque carton. Le stock sera mis à jour uniquement après validation.",
                  style: TextStyle(color: AppTheme.warningColor.withValues(alpha: 0.8), fontSize: 12),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildReceptionItem(int index) {
    final item = _expectedItems[index];
    final isComplete = item['received_qty'] == item['expected_qty'];

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: isComplete ? Colors.green.withValues(alpha: 0.3) : Colors.transparent, width: 2),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(item['name'], style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
              ),
              if (isComplete)
                const Icon(Icons.check_circle, color: Colors.green),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("Attendu (Cartons)", style: TextStyle(color: Colors.grey, fontSize: 10)),
                  Text("${item['expected_qty']}", style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 18)),
                ],
              ),
              Row(
                children: [
                  IconButton(
                    onPressed: item['received_qty'] > 0 ? () {
                      setState(() => item['received_qty']--);
                    } : null,
                    icon: const Icon(Icons.remove_circle_outline, color: Colors.redAccent),
                  ),
                  Container(
                    width: 50,
                    alignment: Alignment.center,
                    child: Text("${item['received_qty']}", 
                      style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 20, color: AppTheme.primaryColor)),
                  ),
                  IconButton(
                    onPressed: item['received_qty'] < item['expected_qty'] ? () {
                      setState(() => item['received_qty']++);
                    } : null,
                    icon: const Icon(Icons.add_circle_outline, color: Colors.green),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildActionArea(bool allReceived) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(30)),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 20)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!allReceived)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Text(
                "Attention : La quantité reçue est inférieure à la commande. Les reliquats seront marqués comme non livrés.",
                style: TextStyle(color: Colors.orange[800], fontSize: 12, fontWeight: FontWeight.bold),
              ),
            ),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton(
              onPressed: () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text("Réception validée ! Stock Magasin mis à jour avec la conversion GNF."),
                    backgroundColor: Colors.green,
                  ),
                );
                Navigator.pop(context);
              },
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryColor, 
                padding: const EdgeInsets.symmetric(vertical: 18),
              ),
              child: const Text("VALIDER L'ENTRÉE EN STOCK", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ),
          ),
        ],
      ),
    );
  }
}
