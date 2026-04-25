import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:autopieces_pro/core/theme/app_theme.dart';
import 'package:autopieces_pro/features/produits/domain/models/product_model.dart';
import 'package:autopieces_pro/features/produits/presentation/screens/product_detail_screen.dart';

class CatalogScreen extends StatefulWidget {
  const CatalogScreen({super.key});

  @override
  State<CatalogScreen> createState() => _CatalogScreenState();
}

class _CatalogScreenState extends State<CatalogScreen> {
  final List<Product> _allProducts = [
    Product(
      id: 1,
      nom: "Plaquettes de frein Avant",
      reference: "TOY-456-FB",
      categorieNom: "Freinage",
      marqueNom: "Toyota",
      prixVente: 450000,
      quantite: 15,
      seuilAlerte: 5,
      codeBarre: "123456789",
      estEnAlerte: false,
    ),
    Product(
      id: 2,
      nom: "Filtre à Huile Corolla",
      reference: "OIL-COR-78",
      categorieNom: "Moteur",
      marqueNom: "Denso",
      prixVente: 85000,
      quantite: 3,
      seuilAlerte: 10,
      codeBarre: "987654321",
      estEnAlerte: true,
    ),
    Product(
      id: 3,
      nom: "Amortisseur Arrière",
      reference: "SUS-AM-002",
      categorieNom: "Suspension",
      marqueNom: "KYB",
      prixVente: 1250000,
      quantite: 0,
      seuilAlerte: 2,
      codeBarre: "555666777",
      estEnAlerte: true,
    ),
  ];

  String _searchQuery = "";
  String _activeFilter = "Tous";

  List<Product> get _filteredProducts {
    List<Product> list = _allProducts.where((p) {
      final matchesSearch =
          p.nom.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          p.reference.toLowerCase().contains(_searchQuery.toLowerCase()) ||
          p.codeBarre.contains(_searchQuery);
      return matchesSearch;
    }).toList();

    if (_activeFilter == "En Rupture") {
      return list.where((p) => p.quantite <= 0).toList();
    } else if (_activeFilter == "Stock Faible") {
      return list.where((p) => p.estEnAlerte && p.quantite > 0).toList();
    } else if (_activeFilter == "Prix Élevé") {
      return list.where((p) => p.prixVente > 500000).toList();
    }
    return list;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppTheme.backgroundColor,
      appBar: AppBar(title: const Text("Catalogue Pièces"), actions: const []),
      body: Column(
        children: [
          _buildSearchBar(),
          _buildFastFilterChips(),
          Expanded(
            child: _filteredProducts.isEmpty
                ? _buildEmptyState()
                : ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: _filteredProducts.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, index) =>
                        _buildProductCard(_filteredProducts[index]),
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _showAddProductForm(),
        backgroundColor: AppTheme.primaryColor,
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.inventory_2_outlined,
            size: 64,
            color: Colors.grey.withValues(alpha: 0.3),
          ),
          const SizedBox(height: 16),
          const Text(
            "Aucune pièce ne correspond à vos filtres",
            style: TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _refController = TextEditingController();
  final TextEditingController _buyPriceController = TextEditingController();
  final TextEditingController _sellPriceController = TextEditingController();
  final TextEditingController _barcodeController = TextEditingController();

  void _showAddProductForm() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(context).viewInsets.bottom,
          left: 20,
          right: 20,
          top: 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              "Ajouter une Pièce",
              style: GoogleFonts.outfit(
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 20),
            _buildField(
              "Nom de la pièce",
              Icons.settings_suggest_outlined,
              _nameController,
            ),
            const SizedBox(height: 12),
            _buildField("Référence Fabricant", Icons.tag, _refController),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: _buildField(
                    "Prix d'achat",
                    Icons.download,
                    _buyPriceController,
                    isNum: true,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildField(
                    "Prix de vente",
                    Icons.upload,
                    _sellPriceController,
                    isNum: true,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            _buildField(
              "Référence Fabricant ou Code-barres",
              Icons.tag,
              _barcodeController,
            ),
            const SizedBox(height: 20),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  if (_nameController.text.isNotEmpty &&
                      _refController.text.isNotEmpty) {
                    setState(() {
                      _allProducts.insert(
                        0,
                        Product(
                          id: DateTime.now().millisecondsSinceEpoch,
                          nom: _nameController.text,
                          reference: _refController.text,
                          prixVente:
                              double.tryParse(_sellPriceController.text) ?? 0,
                          quantite: 0,
                          seuilAlerte: 5,
                          codeBarre: _barcodeController.text,
                          estEnAlerte: true,
                        ),
                      );
                    });
                    _nameController.clear();
                    _refController.clear();
                    _buyPriceController.clear();
                    _sellPriceController.clear();
                    _barcodeController.clear();
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text(
                          "Produit ajouté avec succès au catalogue",
                        ),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  }
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: AppTheme.primaryColor,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: const Text(
                  "ENREGISTRER LA PIÈCE",
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildField(
    String label,
    IconData icon,
    TextEditingController controller, {
    bool isNum = false,
  }) {
    return TextField(
      controller: controller,
      keyboardType: isNum ? TextInputType.number : TextInputType.text,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: AppTheme.primaryColor, size: 20),
        filled: true,
        fillColor: AppTheme.backgroundColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      padding: const EdgeInsets.all(16),
      color: Colors.white,
      child: TextField(
        onChanged: (val) => setState(() => _searchQuery = val),
        decoration: InputDecoration(
          hintText: "Rechercher par nom, réf ou code...",
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

  Widget _buildFastFilterChips() {
    final filters = ["Tous", "En Rupture", "Stock Faible", "Prix Élevé"];
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: filters
            .map((f) => _buildFilterChip(f, _activeFilter == f))
            .toList(),
      ),
    );
  }

  Widget _buildFilterChip(String label, bool isSelected) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: FilterChip(
        label: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.black,
            fontSize: 12,
          ),
        ),
        selected: isSelected,
        onSelected: (bool selected) {
          setState(() => _activeFilter = label);
        },
        backgroundColor: Colors.white,
        selectedColor: AppTheme.primaryColor,
        checkmarkColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: Colors.grey[300]!),
        ),
      ),
    );
  }

  Widget _buildProductCard(Product product) {
    return GestureDetector(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => ProductDetailScreen(product: product),
        ),
      ),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.05),
              blurRadius: 10,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              // Product Image Placeholder
              Container(
                width: 80,
                height: 80,
                decoration: BoxDecoration(
                  color: AppTheme.backgroundColor,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: const Icon(
                  Icons.settings_suggest,
                  color: AppTheme.primaryColor,
                  size: 40,
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      product.nom,
                      style: GoogleFonts.outfit(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      "Réf: ${product.reference} • ${product.marqueNom ?? 'Générique'}",
                      style: const TextStyle(color: Colors.grey, fontSize: 12),
                    ),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(
                          "${product.prixVente.toStringAsFixed(0)} GNF",
                          style: GoogleFonts.outfit(
                            color: AppTheme.primaryColor,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        _buildStockBadge(product),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStockBadge(Product product) {
    Color color;
    String label;

    if (product.quantite <= 0) {
      color = Colors.red;
      label = "RUPTURE";
    } else if (product.estEnAlerte) {
      color = Colors.orange;
      label = "FAIBLE (${product.formatStock()})";
    } else {
      color = Colors.green;
      label = "STOCK (${product.formatStock()})";
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.bold,
          fontSize: 10,
        ),
      ),
    );
  }
}
