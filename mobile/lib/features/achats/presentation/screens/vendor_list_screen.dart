import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

class Supplier {
  final String name;
  final String country;
  final String currency;
  final String type;

  Supplier({required this.name, required this.country, required this.currency, required this.type});
}

class VendorListScreen extends StatefulWidget {
  const VendorListScreen({super.key});

  @override
  State<VendorListScreen> createState() => _VendorListScreenState();
}

class _VendorListScreenState extends State<VendorListScreen> {
  final List<Supplier> _vendors = [
    Supplier(name: "China Parts Ltd", country: "Chine", currency: "USD", type: "International"),
    Supplier(name: "Dubai Auto Hub", country: "Émirats", currency: "USD", type: "International"),
    Supplier(name: "Sékou Distribution", country: "Guinée", currency: "GNF", type: "Local"),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text("Gestion Fournisseurs", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(16),
        itemCount: _vendors.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final v = _vendors[index];
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(16),
              boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10)],
            ),
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.1),
                  child: Text(v.country[0], style: const TextStyle(color: AppTheme.primaryColor, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(v.name, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      Text("${v.country} • ${v.type}", style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(color: Colors.grey[100], borderRadius: BorderRadius.circular(8)),
                  child: Text(v.currency, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddVendorDialog(),
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  void _showAddVendorDialog() {
    final nameCtrl = TextEditingController();
    final countryCtrl = TextEditingController();
    String selectedCurrency = 'GNF';

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Nouveau Fournisseur", style: GoogleFonts.outfit()),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: nameCtrl, decoration: const InputDecoration(labelText: "Nom de l'entreprise")),
            const SizedBox(height: 12),
            TextField(controller: countryCtrl, decoration: const InputDecoration(labelText: "Pays (ex: Chine, Guinée)")),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              value: selectedCurrency,
              decoration: const InputDecoration(labelText: "Devise par défaut"),
              items: const [
                DropdownMenuItem(value: "GNF", child: Text("Franc Guinéen (GNF)")),
                DropdownMenuItem(value: "USD", child: Text("Dollar US (USD)")),
                DropdownMenuItem(value: "EUR", child: Text("Euro (EUR)")),
              ],
              onChanged: (v) => selectedCurrency = v!,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text("ANNULER")),
          ElevatedButton(
            onPressed: () {
              if (nameCtrl.text.isNotEmpty && countryCtrl.text.isNotEmpty) {
                setState(() {
                  _vendors.add(
                    Supplier(
                      name: nameCtrl.text,
                      country: countryCtrl.text,
                      currency: selectedCurrency,
                      type: countryCtrl.text.toLowerCase() == "guinée" ? "Local" : "International"
                    )
                  );
                });
                Navigator.pop(context);
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text("Fournisseur ajouté avec succès")),
                );
              }
            }, 
            child: const Text("CRÉER")
          ),
        ],
      ),
    );
  }
}
