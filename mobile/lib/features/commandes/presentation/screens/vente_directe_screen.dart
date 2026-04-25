import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/features/commandes/data/models/ligne_panier.dart';
import 'package:autopieces_pro/features/clients/presentation/screens/client_list_screen.dart';
import 'package:autopieces_pro/features/clients/domain/models/client_model.dart'
    as model;

class VenteDirecteScreen extends StatefulWidget {
  const VenteDirecteScreen({super.key});

  @override
  State<VenteDirecteScreen> createState() => _VenteDirecteScreenState();
}

class _VenteDirecteScreenState extends State<VenteDirecteScreen> {
  final List<LignePanier> _panier = [];
  double _remise = 0.0;
  model.Client? _selectedClient;

  bool _isRemiseFixe = false;
  final TextEditingController _remiseController = TextEditingController();

  double get _totalBrut => _panier.fold(0, (sum, item) => sum + item.sousTotal);
  double get _totalNet {
    if (_isRemiseFixe) {
      return (_totalBrut - _remise).clamp(0, double.infinity);
    } else {
      return _totalBrut * (1 - _remise / 100);
    }
  }

  @override
  void initState() {
    super.initState();
    _remiseController.text = "0";
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: const Text("Vente au Comptoir"),
        actions: [
          IconButton(
            onPressed: () => setState(() => _panier.clear()),
            icon: const Icon(Icons.delete_sweep_outlined),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildClientSelector(),
          if (_selectedClient != null && _selectedClient!.alerteCredit)
            _buildCreditWarning(),
          _buildSearchBar(),
          Expanded(
            child: _panier.isEmpty
                ? _buildEmptyState()
                : ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: _panier.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, index) =>
                        _buildCartItem(_panier[index]),
                  ),
          ),
          _buildCheckoutSection(),
        ],
      ),
    );
  }

  Widget _buildClientSelector() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(bottom: BorderSide(color: Colors.grey[200]!)),
      ),
      child: Row(
        children: [
          Icon(
            Icons.person_outline,
            color: _selectedClient != null
                ? AppTheme.primaryColor
                : Colors.grey,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: GestureDetector(
              onTap: () {
                // Navigate to client selection list (simulated here)
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const ClientListScreen()),
                );
              },
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _selectedClient?.nom ??
                        "Sélectionner un Client (Optionnel)",
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: _selectedClient != null
                          ? Colors.black
                          : Colors.grey,
                    ),
                  ),
                  if (_selectedClient != null)
                    Text(
                      "Dette courante: ${_selectedClient!.totalDette.toStringAsFixed(0)} GNF",
                      style: const TextStyle(fontSize: 12, color: Colors.grey),
                    ),
                ],
              ),
            ),
          ),
          if (_selectedClient != null)
            IconButton(
              icon: const Icon(Icons.close, size: 20),
              onPressed: () => setState(() => _selectedClient = null),
            )
          else
            const Icon(Icons.chevron_right, color: Colors.grey),
        ],
      ),
    );
  }

  Widget _buildCreditWarning() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      color: Colors.red[50],
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: Colors.red, size: 20),
          const SizedBox(width: 10),
          const Expanded(
            child: Text(
              "ATTENTION : Ce client a dépassé sa limite de crédit !",
              style: TextStyle(
                color: Colors.red,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: TextField(
        decoration: InputDecoration(
          hintText: "Saisir référence ou nom...",
          prefixIcon: const Icon(Icons.search, color: AppTheme.primaryColor),
          filled: true,
          fillColor: AppTheme.backgroundColor,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide.none,
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.shopping_basket_outlined,
            size: 80,
            color: Colors.grey[300],
          ),
          const SizedBox(height: 16),
          Text(
            "Le panier est vide",
            style: GoogleFonts.outfit(fontSize: 18, color: Colors.grey[400]),
          ),
        ],
      ),
    );
  }

  Widget _buildCartItem(LignePanier item) {
    // Live stock check for the warning logic
    final bool isOutOfStock = item.produit.quantite <= 0;
    final bool isLowStock = item.produit.estEnAlerte;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          if (isOutOfStock)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
              decoration: BoxDecoration(
                color: Colors.red[600],
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(16),
                ),
              ),
              child: const Text(
                "ATTENTION : Rupture de stock",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            )
          else if (isLowStock)
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 12),
              decoration: BoxDecoration(
                color: Colors.orange[600],
                borderRadius: const BorderRadius.vertical(
                  top: Radius.circular(16),
                ),
              ),
              child: const Text(
                "Stock faible - Réapprovisionnement suggéré",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Container(
                  width: 50,
                  height: 50,
                  decoration: BoxDecoration(
                    color: AppTheme.backgroundColor,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(
                    Icons.settings_suggest,
                    color: AppTheme.primaryColor,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.produit.nom,
                        style: GoogleFonts.outfit(fontWeight: FontWeight.bold),
                      ),
                      Text(
                        "${item.produit.prixVente.toStringAsFixed(0)} GNF",
                        style: const TextStyle(
                          color: AppTheme.primaryColor,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                _buildQuantityControl(item),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuantityControl(LignePanier item) {
    return Row(
      children: [
        IconButton(
          icon: const Icon(Icons.remove_circle_outline, size: 20),
          onPressed: () => setState(() {
            if (item.quantite > 1) item.quantite--;
          }),
        ),
        Text(
          "${item.quantite}",
          style: GoogleFonts.outfit(fontWeight: FontWeight.bold),
        ),
        IconButton(
          icon: const Icon(
            Icons.add_circle_outline,
            size: 20,
            color: AppTheme.primaryColor,
          ),
          onPressed: () => setState(() => item.quantite++),
        ),
      ],
    );
  }

  Widget _buildCheckoutSection() {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(30)),
        boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 10)],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text("Sous-total", style: TextStyle(fontSize: 16)),
              Text(
                "${_totalBrut.toStringAsFixed(0)} GNF",
                style: const TextStyle(fontSize: 16),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Text("Rabais / Remise", style: TextStyle(fontSize: 14)),
                  const SizedBox(width: 8),
                  GestureDetector(
                    onTap: () => setState(() => _isRemiseFixe = !_isRemiseFixe),
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(20),
                        border: Border.all(color: AppTheme.primaryColor),
                      ),
                      child: Text(
                        _isRemiseFixe ? "GNF" : "%",
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 10,
                          color: AppTheme.primaryColor,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              SizedBox(
                width: 100,
                child: TextField(
                  controller: _remiseController,
                  keyboardType: TextInputType.number,
                  textAlign: TextAlign.end,
                  decoration: InputDecoration(
                    suffixText: _isRemiseFixe ? " GNF" : " %",
                    contentPadding: EdgeInsets.zero,
                  ),
                  onChanged: (val) =>
                      setState(() => _remise = double.tryParse(val) ?? 0),
                ),
              ),
            ],
          ),
          const Divider(height: 32),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "Total Net",
                style: GoogleFonts.outfit(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                "${_totalNet.toStringAsFixed(0)} GNF",
                style: GoogleFonts.outfit(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppTheme.primaryColor,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _panier.isEmpty ? null : _showPaymentDialog,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryColor,
              minimumSize: const Size(double.infinity, 60),
            ),
            child: const Text("VALIDER LA VENTE"),
          ),
        ],
      ),
    );
  }

  void _showPaymentDialog() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => _PaymentBottomSheet(total: _totalNet),
    );
  }
}

class _PaymentBottomSheet extends StatefulWidget {
  final double total;
  const _PaymentBottomSheet({required this.total});

  @override
  State<_PaymentBottomSheet> createState() => _PaymentBottomSheetState();
}

class _PaymentBottomSheetState extends State<_PaymentBottomSheet> {
  String _modeSelected = 'CASH';
  final _amountController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _amountController.text = widget.total.toStringAsFixed(0);
  }

  @override
  Widget build(BuildContext context) {
    double paye = double.tryParse(_amountController.text) ?? 0;
    double reste = widget.total - paye;

    return Padding(
      padding: EdgeInsets.fromLTRB(
        24,
        24,
        24,
        MediaQuery.of(context).viewInsets.bottom + 24,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Finaliser le paiement",
            style: GoogleFonts.outfit(
              fontSize: 22,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 24),
          Text(
            "Mode de règlement",
            style: GoogleFonts.outfit(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _buildModeOption(Icons.money, "Espèces", 'CASH'),
              const SizedBox(width: 12),
              _buildModeOption(Icons.smartphone, "Mobile Money", 'MOBILE'),
            ],
          ),
          const SizedBox(height: 24),
          Text(
            "Montant versé (GNF)",
            style: GoogleFonts.outfit(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _amountController,
            keyboardType: TextInputType.number,
            style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            decoration: const InputDecoration(
              suffixIcon: Icon(Icons.edit, size: 20),
            ),
            onChanged: (_) => setState(() {}),
          ),
          const SizedBox(height: 16),
          if (reste > 0)
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.warningColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.warning_amber_rounded,
                    color: AppTheme.warningColor,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    "Délivré à crédit. Reste dû : ${reste.toStringAsFixed(0)} GNF",
                    style: const TextStyle(
                      color: AppTheme.warningColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          const SizedBox(height: 32),
          ElevatedButton(
            onPressed: () async {
              try {
                // Showing quick loading
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text("Enregistrement de la vente BSG..."),
                    duration: Duration(seconds: 1),
                  ),
                );

                // This logic should be moved to a controller, but doing it here for the POC
                // In a real app, use BLoC/Provider
                Navigator.pop(context); // Close sheet
                Navigator.pop(context); // Go back to Dashboard

                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text("✅ Vente réussie ! Stock mis à jour."),
                    backgroundColor: Colors.green,
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              } catch (e) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text("Erreur: ${e.toString()}"),
                    backgroundColor: Colors.red,
                  ),
                );
              }
            },
            child: const Text("ENREGISTRER LA TRANSACTION"),
          ),
        ],
      ),
    );
  }

  Widget _buildModeOption(IconData icon, String label, String value) {
    bool isSelected = _modeSelected == value;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _modeSelected = value),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            color: isSelected ? AppTheme.primaryColor : Colors.white,
            border: Border.all(
              color: isSelected ? AppTheme.primaryColor : Colors.grey[300]!,
            ),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Column(
            children: [
              Icon(icon, color: isSelected ? Colors.white : Colors.grey),
              const SizedBox(height: 8),
              Text(
                label,
                style: TextStyle(
                  color: isSelected ? Colors.white : Colors.grey,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
