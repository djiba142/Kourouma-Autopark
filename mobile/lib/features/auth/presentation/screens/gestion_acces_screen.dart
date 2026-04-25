import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';

class GestionAccesScreen extends StatefulWidget {
  const GestionAccesScreen({super.key});

  @override
  State<GestionAccesScreen> createState() => _GestionAccesScreenState();
}

class _GestionAccesScreenState extends State<GestionAccesScreen> {
  // Mock data for UI 
  final List<Map<String, String>> _employees = [
    {'nom': 'Moussa Camara', 'email': 'moussa@bsg.com', 'role': 'EMPLOYE', 'status': 'Actif'},
    {'nom': 'Aminata Diallo', 'email': 'aminata@bsg.com', 'role': 'EMPLOYE', 'status': 'Actif'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(title: const Text("Gestion des Accès")),
      body: ListView.separated(
        padding: const EdgeInsets.all(20),
        itemCount: _employees.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final emp = _employees[index];
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppTheme.surfaceColor,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Row(
              children: [
                CircleAvatar(
                  backgroundColor: AppTheme.primaryColor.withValues(alpha: 0.2),
                  child: Text(emp['nom']![0], style: const TextStyle(color: AppTheme.primaryColor, fontWeight: FontWeight.bold)),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(emp['nom']!, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: Colors.white)),
                      Text(emp['email']!, style: TextStyle(color: Colors.grey[400], fontSize: 13)),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.successColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    emp['status']!, 
                    style: const TextStyle(color: AppTheme.successColor, fontSize: 10, fontWeight: FontWeight.bold)
                  ),
                ),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showAddEmployeeDialog,
        backgroundColor: AppTheme.primaryColor,
        icon: const Icon(Icons.person_add_alt_1, color: Colors.white),
        label: const Text("Attribuer un accès", style: TextStyle(color: Colors.white)),
      ),
    );
  }

  void _showAddEmployeeDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surfaceColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(30))),
      builder: (context) => Padding(
        padding: EdgeInsets.fromLTRB(24, 24, 24, MediaQuery.of(context).viewInsets.bottom + 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Nouvel Employé", style: GoogleFonts.outfit(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white)),
            const SizedBox(height: 24),
            const TextField(
              decoration: InputDecoration(labelText: "Nom complet", prefixIcon: Icon(Icons.person_outline)),
            ),
            const SizedBox(height: 16),
            const TextField(
              decoration: InputDecoration(labelText: "Email BSG", prefixIcon: Icon(Icons.email_outlined)),
            ),
            const SizedBox(height: 16),
            const TextField(
              obscureText: true,
              decoration: InputDecoration(labelText: "Mot de passe initial", prefixIcon: Icon(Icons.lock_outline)),
            ),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("CRÉER L'ACCÈS"),
            ),
          ],
        ),
      ),
    );
  }
}
