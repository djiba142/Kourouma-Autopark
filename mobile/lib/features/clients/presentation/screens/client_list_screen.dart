import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:url_launcher/url_launcher.dart';

class ClientListScreen extends StatefulWidget {
  const ClientListScreen({super.key});

  @override
  State<ClientListScreen> createState() => _ClientListScreenState();
}

class _ClientListScreenState extends State<ClientListScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _filter = "";

  // Mock Data for UI demonstration
  final List<Map<String, dynamic>> _mockClients = [
    {
      'nom': 'Mamady Condé',
      'tel': '+224 620 12 34 56',
      'dette': '450,000 GNF',
      'limite': '1,000,000 GNF',
      'statut': 'MAUVAIS',
      'alerte': true,
      'adresse': 'Sandervalia, Kaloum',
      'date_creation': '12/03/2026',
    },
    {
      'nom': 'Fatoumata Camara',
      'tel': '+224 664 98 76 54',
      'dette': '0 GNF',
      'limite': '5,000,000 GNF',
      'statut': 'BON',
      'alerte': false,
      'adresse': 'Lambanyi, Ratoma',
      'date_creation': '25/02/2026',
    },
    {
      'nom': 'Ousmane Sylla',
      'tel': '+224 621 11 22 33',
      'dette': '125,000 GNF',
      'limite': '500,000 GNF',
      'statut': 'MOYEN',
      'alerte': false,
      'adresse': 'Koubia',
      'date_creation': '01/01/2026',
    },
  ];

  List<Map<String, dynamic>> get _filteredClients {
    if (_filter.isEmpty) return _mockClients;
    return _mockClients.where((client) {
      final name = client['nom'].toString().toLowerCase();
      final tel = client['tel'].toString().replaceAll(' ', '');
      final query = _filter.toLowerCase();
      return name.contains(query) || tel.contains(query);
    }).toList();
  }
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0A0A0A),
      appBar: AppBar(
        title: Text("Gestion Clients", style: GoogleFonts.outfit(fontSize: 18, fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 8),
            child: TextField(
              controller: _searchController,
              onChanged: (value) => setState(() => _filter = value),
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: "Rechercher un numéro ou un nom...",
                hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                prefixIcon: const Icon(Icons.search, color: AppTheme.primaryColor),
                suffixIcon: _filter.isNotEmpty 
                  ? IconButton(
                      icon: const Icon(Icons.close, color: Colors.grey, size: 18),
                      onPressed: () {
                        _searchController.clear();
                        setState(() => _filter = "");
                      },
                    )
                  : null,
                filled: true,
                fillColor: AppTheme.surfaceColor,
                contentPadding: const EdgeInsets.symmetric(vertical: 0),
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
              ),
            ),
          ),
          Expanded(
            child: _filteredClients.isEmpty 
              ? _buildEmptyState()
              : ListView.builder(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _filteredClients.length,
                  itemBuilder: (context, index) {
                    final client = _filteredClients[index];
                    return _buildClientCard(client);
                  },
                ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddClientForm(),
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.person_add_alt_1_rounded, color: Colors.white),
      ),
    );
  }  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _addressController = TextEditingController();

  void _showAddClientForm() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppTheme.surfaceColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
          left: 20, right: 20, top: 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Nouveau Client", style: GoogleFonts.outfit(color: Colors.black87, fontSize: 20, fontWeight: FontWeight.bold)),
            const SizedBox(height: 20),
            _buildField("Nom complet", Icons.person_outline, _nameController),
            const SizedBox(height: 12),
            _buildField("Numéro de téléphone", Icons.phone_android_outlined, _phoneController, isPhone: true),
            const SizedBox(height: 12),
            _buildField("Email (Optionnel)", Icons.email_outlined, _emailController),
            const SizedBox(height: 12),
            _buildField("Adresse / Quartier", Icons.location_on_outlined, _addressController),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  if (_nameController.text.isNotEmpty && _phoneController.text.isNotEmpty) {
                    setState(() {
                      _mockClients.insert(0, {
                        'nom': _nameController.text,
                        'tel': _phoneController.text,
                        'dette': '0 GNF',
                        'statut': 'BON',
                        'alerte': false,
                        'adresse': _addressController.text,
                        'date_creation': '04/04/2026',
                      });
                    });
                    _nameController.clear();
                    _phoneController.clear();
                    _emailController.clear();
                    _addressController.clear();
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text("Profil client créé avec succès"), behavior: SnackBarBehavior.floating),
                    );
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
                child: const Text("CRÉER LE PROFIL", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildField(String label, IconData icon, TextEditingController controller, {bool isPhone = false}) {
    return TextField(
      controller: controller,
      keyboardType: isPhone ? TextInputType.phone : TextInputType.text,
      style: const TextStyle(color: Colors.black87),
      decoration: InputDecoration(
        labelText: label,
        labelStyle: const TextStyle(color: Colors.grey, fontSize: 13),
        prefixIcon: Icon(icon, color: Colors.grey, size: 20),
        filled: true,
        fillColor: Colors.black.withValues(alpha: 0.05),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.person_search_outlined, size: 60, color: Colors.white.withValues(alpha: 0.1)),
          const SizedBox(height: 16),
          const Text("Aucun client trouvé", style: TextStyle(color: Colors.grey)),
        ],
      ),
    );
  }

  Widget _buildClientCard(Map<String, dynamic> client) {
    Color statusColor;
    switch (client['statut']) {
      case 'BON': statusColor = Colors.greenAccent; break;
      case 'MOYEN': statusColor = Colors.orangeAccent; break;
      case 'MAUVAIS': statusColor = Colors.redAccent; break;
      default: statusColor = Colors.grey;
    }

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: client['alerte'] ? Colors.red.withValues(alpha: 0.2) : Colors.black.withValues(alpha: 0.03)),
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.05), blurRadius: 10)],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                backgroundColor: statusColor.withValues(alpha: 0.1),
                child: Text(client['nom'][0], style: TextStyle(color: statusColor, fontWeight: FontWeight.bold)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(client['nom'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16)),
                    Text(client['tel'], style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(color: statusColor.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(8)),
                child: Text(client['statut'], style: TextStyle(color: statusColor, fontSize: 10, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (client['adresse'] != null)
            Row(
              children: [
                const Icon(Icons.location_on_outlined, color: Colors.grey, size: 14),
                const SizedBox(width: 8),
                Text(client['adresse'], style: const TextStyle(color: Colors.grey, fontSize: 12)),
              ],
            ),
          const Divider(height: 24, color: Colors.black12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text("SOLDE / LIMITE CRÉDIT", style: TextStyle(color: Colors.grey, fontSize: 10, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Text(client['dette'], style: TextStyle(color: client['alerte'] ? Colors.red : AppTheme.primaryColor, fontWeight: FontWeight.bold, fontSize: 14)),
                        const Text(" / ", style: TextStyle(color: Colors.grey)),
                        Text(client['limite'] ?? '0 GNF', style: const TextStyle(color: Colors.grey, fontSize: 13)),
                        if (client['alerte'])
                          const Padding(
                            padding: EdgeInsets.only(left: 8.0),
                            child: Icon(Icons.warning_amber_rounded, color: Colors.red, size: 16),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              Row(
                children: [
                  IconButton(
                    icon: const Icon(Icons.message_outlined, color: Colors.greenAccent, size: 20),
                    onPressed: () async {
                      final cleanTel = client['tel'].toString().replaceAll(RegExp(r'[^0-9]'), '');
                      // URL universelle WhatsApp
                      final whatsappUrl = "https://wa.me/$cleanTel?text=Bonjour ${client['nom']}, BSG vous contacte concernant votre solde...";
                      final uri = Uri.parse(whatsappUrl);
                      
                      try {
                        await launchUrl(uri, mode: LaunchMode.externalApplication);
                      } catch (e) {
                         if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text("Action impossible sur ce support")),
                          );
                        }
                      }
                    },
                  ),
                  IconButton(
                    icon: const Icon(Icons.call_outlined, color: Colors.blueAccent, size: 20),
                    onPressed: () async {
                      final cleanTel = client['tel'].toString().replaceAll(RegExp(r'[^0-9+]'), '');
                      final phoneUrl = "tel:$cleanTel";
                      final uri = Uri.parse(phoneUrl);
                      if (await canLaunchUrl(uri)) {
                        await launchUrl(uri);
                      }
                    },
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            "Client créé le : ${client['date_creation'] ?? '01/01/2026'}", 
            style: const TextStyle(color: Colors.white24, fontSize: 9, fontStyle: FontStyle.italic),
          ),
        ],
      ),
    );
  }
}
