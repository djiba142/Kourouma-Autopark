class Product {
  final int id;
  final String nom;
  final String reference;
  final String? categorieNom;
  final String? marqueNom;
  final double? prixAchat; // Nullable for non-admins
  final double prixVente;
  final int quantite;
  final int seuilAlerte;
  final String codeBarre;
  final String? image;
  final bool estEnAlerte;
  final double? benefice;
  final double? tauxMarge;

  final String unitePrincipale;
  final String uniteSecondaire;
  final int conversionUnit;
  final String achatDevise;
  final double? prixAchatDevise;
  final double? tauxChangeAchat;

  Product({
    required this.id,
    required this.nom,
    required this.reference,
    this.categorieNom,
    this.marqueNom,
    this.prixAchat,
    required this.prixVente,
    required this.quantite,
    required this.seuilAlerte,
    required this.codeBarre,
    this.image,
    required this.estEnAlerte,
    this.benefice,
    this.tauxMarge,
    this.unitePrincipale = 'CARTON',
    this.uniteSecondaire = 'PIECE',
    this.conversionUnit = 1,
    this.achatDevise = 'GNF',
    this.prixAchatDevise,
    this.tauxChangeAchat,
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id'],
      nom: json['nom'],
      reference: json['reference'],
      categorieNom: json['categorie_nom'],
      marqueNom: json['marque_nom'],
      prixAchat: json['prix_achat'] != null ? double.parse(json['prix_achat'].toString()) : null,
      prixVente: double.parse(json['prix_vente'].toString()),
      quantite: json['quantite'] ?? 0,
      seuilAlerte: json['seuil_alerte'] ?? 5,
      codeBarre: json['code_barre'] ?? '',
      image: json['image'],
      estEnAlerte: json['est_en_alerte'] ?? false,
      benefice: json['benefice'] != null ? double.parse(json['benefice'].toString()) : null,
      tauxMarge: json['taux_marge'] != null ? double.parse(json['taux_marge'].toString()) : null,
      unitePrincipale: json['unite_principale'] ?? 'CARTON',
      uniteSecondaire: json['unite_secondaire'] ?? 'PIECE',
      conversionUnit: json['conversion_unit'] ?? 1,
      achatDevise: json['achat_devise'] ?? 'GNF',
      prixAchatDevise: json['prix_achat_devise'] != null ? double.parse(json['prix_achat_devise'].toString()) : null,
      tauxChangeAchat: json['taux_change_achat'] != null ? double.parse(json['taux_change_achat'].toString()) : null,
    );
  }

  String formatStock() {
    if (conversionUnit <= 1) return "$quantite $uniteSecondaire";
    int cartons = quantite ~/ conversionUnit;
    int pieces = quantite % conversionUnit;
    
    if (cartons > 0 && pieces > 0) {
      return "$cartons $unitePrincipale + $pieces $uniteSecondaire";
    } else if (cartons > 0) {
      return "$cartons $unitePrincipale";
    } else {
      return "$pieces $uniteSecondaire";
    }
  }
}

class PriceHistory {
  final int id;
  final double ancienPrix;
  final double nouveauPrix;
  final String modifiePar;
  final DateTime dateModification;

  PriceHistory({
    required this.id,
    required this.ancienPrix,
    required this.nouveauPrix,
    required this.modifiePar,
    required this.dateModification,
  });

  factory PriceHistory.fromJson(Map<String, dynamic> json) {
    return PriceHistory(
      id: json['id'],
      ancienPrix: double.parse(json['ancien_prix'].toString()),
      nouveauPrix: double.parse(json['nouveau_prix'].toString()),
      modifiePar: json['modifie_par_nom'] ?? "Inconnu",
      dateModification: DateTime.parse(json['date_modification']),
    );
  }
}
