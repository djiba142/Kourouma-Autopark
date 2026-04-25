import 'dart:io';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/features/commandes/domain/models/commande_model.dart';
import 'package:autopieces_pro/features/commandes/data/repositories/commande_repository.dart';
import 'package:autopieces_pro/core/network/api_client.dart';
import 'package:autopieces_pro/features/factures/presentation/screens/facture_screen.dart';

class OrderDetailScreen extends StatefulWidget {
  final Commande order;
  const OrderDetailScreen({super.key, required this.order});

  @override
  State<OrderDetailScreen> createState() => _OrderDetailScreenState();
}

class _OrderDetailScreenState extends State<OrderDetailScreen> {
  late Commande _currentOrder;
  final List<int> _pickedItems = [];

  @override
  void initState() {
    super.initState();
    _currentOrder = widget.order;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text("Détails Commande", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => FactureScreen(commande: _currentOrder))),
            icon: const Icon(Icons.picture_as_pdf_outlined),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            _buildOrderStatusCard(),
            const SizedBox(height: 16),
            _buildClientInfo(),
            const SizedBox(height: 16),
            _buildItemsList(),
            if (_currentOrder.paiements.isNotEmpty) ...[
              const SizedBox(height: 16),
              _buildPaymentHistory(),
            ],
            const SizedBox(height: 100),
          ],
        ),
      ),
      bottomSheet: _buildActionArea(),
    );
  }

  Widget _buildOrderStatusCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppTheme.primaryColor.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppTheme.primaryColor.withValues(alpha: 0.1)),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(color: AppTheme.primaryColor, borderRadius: BorderRadius.circular(12)),
            child: const Icon(Icons.receipt_long, color: Colors.white),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_currentOrder.numero, style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 18)),
                Text("Commandée le ${_currentOrder.dateCreation.day}/${_currentOrder.dateCreation.month}", 
                  style: TextStyle(color: Colors.grey[600], fontSize: 12)),
              ],
            ),
          ),
          _buildStatusBadge(_currentOrder.statut),
        ],
      ),
    );
  }

  Widget _buildClientInfo() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("CLIENT", style: GoogleFonts.outfit(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          Row(
            children: [
              const CircleAvatar(radius: 15, backgroundColor: AppTheme.primaryColor, child: Icon(Icons.person, size: 16, color: Colors.white)),
              const SizedBox(width: 12),
              Text(_currentOrder.clientDetails ?? "Client Comptoir", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildItemsList() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("ARTICLES", style: GoogleFonts.outfit(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.bold)),
              Text("${_currentOrder.lignes.length} Réf.", style: const TextStyle(fontSize: 12, color: AppTheme.primaryColor)),
            ],
          ),
          const Divider(height: 24),
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: _currentOrder.lignes.length,
            separatorBuilder: (_, __) => const Divider(height: 24),
            itemBuilder: (context, index) {
              final item = _currentOrder.lignes[index];
              final isPicked = _pickedItems.contains(index);
              
              return InkWell(
                onTap: () {
                  if (_currentOrder.statut == OrderStatus.enPreparation) {
                    setState(() {
                      if (isPicked) {
                        _pickedItems.remove(index);
                      } else {
                        _pickedItems.add(index);
                      }
                    });
                  }
                },
                child: Row(
                  children: [
                    if (_currentOrder.statut == OrderStatus.enPreparation)
                      Icon(isPicked ? Icons.check_box : Icons.check_box_outline_blank, color: isPicked ? Colors.green : Colors.grey),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(item.produitDetails?.nom ?? "Produit # ${item.produitId}", style: const TextStyle(fontWeight: FontWeight.bold)),
                          Text("Ref: ${item.produitDetails?.reference ?? 'N/A'}", style: const TextStyle(fontSize: 10, color: Colors.grey)),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text("x${item.quantite}", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
                        Text("${item.sousTotal.toInt()} GNF", style: const TextStyle(fontSize: 12, color: AppTheme.primaryColor)),
                      ],
                    ),
                  ],
                ),
              );
            },
          ),
          const Divider(height: 32),
          _buildTotalRow("Total Brut", "${_currentOrder.totalHt.toInt()} GNF", isBold: false),
          _buildTotalRow("Remise", "-${_currentOrder.remise.toInt()} GNF", color: Colors.red),
          _buildTotalRow("NET À PAYER", "${_currentOrder.totalTtc.toInt()} GNF", isBold: true, color: AppTheme.primaryColor),
          _buildTotalRow("RESTE À PAYER", "${_currentOrder.resteAPayer.toInt()} GNF", isBold: true, color: Colors.orange),
        ],
      ),
    );
  }

  Widget _buildPaymentHistory() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(16)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("HISTORIQUE PAIEMENTS", style: GoogleFonts.outfit(fontSize: 12, color: Colors.grey, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ..._currentOrder.paiements.map((p) => Padding(
            padding: const EdgeInsets.only(bottom: 8.0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text("${p.date.day}/${p.date.month} - ${p.mode}", style: const TextStyle(fontSize: 12)),
                Text("${p.montant.toInt()} GNF", style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12)),
              ],
            ),
          )),
        ],
      ),
    );
  }

  Widget _buildTotalRow(String label, String value, {bool isBold = false, Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(fontWeight: isBold ? FontWeight.bold : FontWeight.normal, fontSize: isBold ? 14 : 12)),
          Text(value, style: GoogleFonts.outfit(fontWeight: isBold ? FontWeight.bold : FontWeight.normal, fontSize: isBold ? 16 : 12, color: color)),
        ],
      ),
    );
  }

  Widget _buildActionArea() {
    bool isAdmin = true;
    bool hasRemaining = _currentOrder.resteAPayer > 0;
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.1), blurRadius: 20)],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (hasRemaining)
            _buildActionButton("ENREGISTRER PAIEMENT", Icons.payments, Colors.orange, onPressed: _showPaymentDialog),
          
          const SizedBox(height: 10),

          if (_currentOrder.statut == OrderStatus.enAttente && isAdmin)
            _buildActionButton("VALIDER LA COMMANDE", Icons.check_circle, Colors.green),
          
          if (_currentOrder.statut == OrderStatus.validee)
            _buildActionButton("COMMENCER PRÉPARATION", Icons.inventory_2, Colors.purple),
            
          if (_currentOrder.statut == OrderStatus.enPreparation)
            _buildActionButton("CONFIRMER PRÊTE", Icons.mark_as_unread, Colors.indigo, isEnabled: _pickedItems.length == _currentOrder.lignes.length),
            
          if (_currentOrder.statut == OrderStatus.prete)
            _buildActionButton("EXPÉDIER LE COLIS", Icons.local_shipping, AppTheme.primaryColor),
        ],
      ),
    );
  }

  void _showPaymentDialog() {
    showDialog(
      context: context,
      builder: (context) => _PaymentEntryDialog(
        order: _currentOrder,
        onSuccess: () {
          // Success logic (ideally re-fetch order)
          Navigator.pop(context);
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Paiement enregistré")));
        },
      ),
    );
  }

  Widget _buildActionButton(String label, IconData icon, Color color, {bool isEnabled = true, VoidCallback? onPressed}) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton.icon(
        onPressed: isEnabled ? (onPressed ?? () {}) : null,
        icon: Icon(icon, color: Colors.white),
        label: Text(label, style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          padding: const EdgeInsets.symmetric(vertical: 16),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          disabledBackgroundColor: Colors.grey[300],
        ),
      ),
    );
  }

  Widget _buildStatusBadge(OrderStatus status) {
    Color color;
    String text;
    switch (status) {
      case OrderStatus.enAttente: color = Colors.orange; text = "EN ATTENTE"; break;
      case OrderStatus.validee: color = Colors.blue; text = "VALIDÉE"; break;
      case OrderStatus.enPreparation: color = Colors.purple; text = "PRÉPARATION"; break;
      case OrderStatus.prete: color = Colors.indigo; text = "PRÊTE"; break;
      case OrderStatus.expediee: color = Colors.indigo; text = "EXPÉDIÉE"; break;
      case OrderStatus.livree: color = Colors.green; text = "LIVRÉE"; break;
      default: color = Colors.grey; text = "ANNULÉE";
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(20)),
      child: Text(text, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }
}

class _PaymentEntryDialog extends StatefulWidget {
  final Commande order;
  final VoidCallback onSuccess;

  const _PaymentEntryDialog({required this.order, required this.onSuccess});

  @override
  State<_PaymentEntryDialog> createState() => _PaymentEntryDialogState();
}

class _PaymentEntryDialogState extends State<_PaymentEntryDialog> {
  final _amountController = TextEditingController();
  final _refController = TextEditingController();
  String _selectedMode = 'CASH';
  File? _proofImage;
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _amountController.text = widget.order.resteAPayer.toInt().toString();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text("Enregistrer Paiement", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _amountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: "Montant (GNF)", hintText: "Ex: 500000"),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _selectedMode,
              items: const [
                DropdownMenuItem(value: 'CASH', child: Text('Espèces')),
                DropdownMenuItem(value: 'MOBILE_MONEY', child: Text('Mobile Money')),
                DropdownMenuItem(value: 'VIREMENT', child: Text('Virement')),
              ],
              onChanged: (v) => setState(() => _selectedMode = v!),
              decoration: const InputDecoration(labelText: "Mode"),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: _refController,
              decoration: const InputDecoration(labelText: "Référence (Optionnel)", hintText: "N° Transaction"),
            ),
            const SizedBox(height: 20),
            GestureDetector(
              onTap: _pickImage,
              child: Container(
                height: 100,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: Colors.grey[100],
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: Colors.grey[300]!),
                ),
                child: _proofImage != null 
                  ? ClipRRect(borderRadius: BorderRadius.circular(12), child: Image.file(_proofImage!, fit: BoxFit.cover))
                  : const Icon(Icons.camera_alt, color: Colors.grey),
              ),
            ),
            const Text("Capture de preuve recommandée", style: TextStyle(fontSize: 10, color: Colors.grey)),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text("ANNULER")),
        if (_isLoading)
          const CircularProgressIndicator()
        else
          ElevatedButton(onPressed: _submit, child: const Text("VALIDER")),
      ],
    );
  }

  Future<void> _pickImage() async {
    final picked = await ImagePicker().pickImage(source: ImageSource.camera);
    if (picked != null) setState(() => _proofImage = File(picked.path));
  }

  Future<void> _submit() async {
    setState(() => _isLoading = true);
    try {
      final repo = CommandeRepository(ApiClient());
      await repo.registerPayment(
        orderId: widget.order.id!,
        montant: double.parse(_amountController.text),
        mode: _selectedMode,
        reference: _refController.text,
        proofPath: _proofImage?.path,
      );
      widget.onSuccess();
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text("Erreur: $e")));
    } finally {
      setState(() => _isLoading = false);
    }
  }
}
