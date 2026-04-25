import 'package:autopieces_pro/shared/models/produit.dart';

class LignePanier {
  final Produit produit;
  int quantite;

  LignePanier({required this.produit, this.quantite = 1});

  double get sousTotal => produit.prixVente * quantite;
}
