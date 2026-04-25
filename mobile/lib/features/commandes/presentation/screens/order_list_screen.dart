import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/features/commandes/domain/models/commande_model.dart';
import 'package:autopieces_pro/features/commandes/presentation/screens/order_detail_screen.dart';

class OrderListScreen extends StatefulWidget {
  const OrderListScreen({super.key});

  @override
  State<OrderListScreen> createState() => _OrderListScreenState();
}

class _OrderListScreenState extends State<OrderListScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(
        title: Text("Suivi Commandes", style: GoogleFonts.outfit(fontWeight: FontWeight.bold)),
        bottom: TabBar(
          controller: _tabController,
          isScrollable: true,
          labelColor: AppTheme.primaryColor,
          unselectedLabelColor: Colors.grey,
          indicatorColor: AppTheme.primaryColor,
          tabs: const [
            Tab(text: "TOUTES"),
            Tab(text: "EN ATTENTE"),
            Tab(text: "PRÉPARATION"),
            Tab(text: "LIVRÉES"),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          _buildOrderList(null),
          _buildOrderList(OrderStatus.enAttente),
          _buildOrderList(OrderStatus.enPreparation),
          _buildOrderList(OrderStatus.livree),
        ],
      ),
    );
  }

  Widget _buildOrderList(OrderStatus? filter) {
    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: 5, // Mock data for now
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        return _buildOrderCard(index, filter ?? OrderStatus.enAttente);
      },
    );
  }

  Widget _buildOrderCard(int index, OrderStatus status) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          )
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text("BSG-240404000${index + 1}", 
                style: GoogleFonts.outfit(fontWeight: FontWeight.bold, fontSize: 16)),
              _buildStatusBadge(status),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.person_outline, size: 14, color: Colors.grey),
              const SizedBox(width: 4),
              Text("Client: Diaby Transport", 
                style: TextStyle(color: Colors.grey[600], fontSize: 12)),
            ],
          ),
          const Divider(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("TOTAL À PAYER", style: TextStyle(color: Colors.grey, fontSize: 10)),
                  Text("1 250 000 GNF", 
                    style: GoogleFonts.outfit(
                      fontWeight: FontWeight.bold, 
                      color: AppTheme.primaryColor,
                      fontSize: 16
                    )),
                ],
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.push(context, MaterialPageRoute(builder: (_) => OrderDetailScreen(
                    order: Commande(
                      numero: "BSG-240404000${index + 1}",
                      statut: status,
                      statutPaiement: PaymentStatus.nonPaye,
                      typeVente: "COMMANDE",
                      totalHt: 1250000,
                      typeRemise: DiscountType.pourcent,
                      remise: 0,
                      totalTtc: 1250000,
                      resteAPayer: 1250000,
                      lignes: [
                        LigneCommande(produitId: 1, quantite: 2, prixUnitaire: 500000, sousTotal: 1000000),
                      ],
                      paiements: const [],
                      dateCreation: DateTime.now(),
                    ),
                  )));
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                  minimumSize: const Size(100, 36),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  elevation: 0,
                ),
                child: const Text("DÉTAILS", 
                  style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
              ),
            ],
          ),
        ],
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
      case OrderStatus.expediee: color = Colors.indigo; text = "EXPÉDIÉE"; break;
      case OrderStatus.livree: color = Colors.green; text = "LIVRÉE"; break;
      default: color = Colors.grey; text = "ANNULÉE";
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(text, 
        style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.bold)),
    );
  }
}
