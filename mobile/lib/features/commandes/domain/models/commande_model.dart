import 'package:autopieces_pro/features/produits/domain/models/product_model.dart';

enum OrderStatus {
  enAttente,
  validee,
  enPreparation,
  prete,
  expediee,
  livree,
  annulee
}

enum PaymentStatus {
  nonPaye,
  partiel,
  paye
}

enum DiscountType {
  fixe,
  pourcent
}

class Commande {
  final int? id;
  final String numero;
  final int? clientId;
  final String? clientDetails;
  final OrderStatus statut;
  final PaymentStatus statutPaiement;
  final String typeVente;
  final double totalHt;
  final DiscountType typeRemise;
  final double remise;
  final double totalTtc;
  final double resteAPayer;
  final List<LigneCommande> lignes;
  final List<PaymentRecord> paiements;
  final DateTime dateCreation;
  final String? notes;

  Commande({
    this.id,
    required this.numero,
    this.clientId,
    this.clientDetails,
    required this.statut,
    required this.statutPaiement,
    required this.typeVente,
    required this.totalHt,
    required this.typeRemise,
    required this.remise,
    required this.totalTtc,
    required this.resteAPayer,
    required this.lignes,
    required this.paiements,
    required this.dateCreation,
    this.notes,
  });

  factory Commande.fromJson(Map<String, dynamic> json) {
    return Commande(
      id: json['id'],
      numero: json['numero'] ?? 'PENDING',
      clientId: json['client'],
      clientDetails: json['client_details'],
      statut: _parseStatus(json['statut']),
      statutPaiement: _parsePaymentStatus(json['statut_paiement']),
      typeVente: json['type_vente'],
      totalHt: double.parse(json['total_ht'].toString()),
      typeRemise: json['type_remise'] == 'POURCENT' ? DiscountType.pourcent : DiscountType.fixe,
      remise: double.parse(json['remise'].toString()),
      totalTtc: double.parse(json['total_ttc'].toString()),
      resteAPayer: double.parse(json['reste_a_payer'].toString()),
      lignes: (json['lignes'] as List? ?? []).map((l) => LigneCommande.fromJson(l)).toList(),
      paiements: (json['paiements'] as List? ?? []).map((p) => PaymentRecord.fromJson(p)).toList(),
      dateCreation: DateTime.parse(json['date_creation']),
      notes: json['notes'],
    );
  }

  static OrderStatus _parseStatus(String status) {
    switch (status) {
      case 'EN_ATTENTE': return OrderStatus.enAttente;
      case 'VALIDEE': return OrderStatus.validee;
      case 'EN_PREPARATION': return OrderStatus.enPreparation;
      case 'PRETE': return OrderStatus.prete;
      case 'EXPEDIEE': return OrderStatus.expediee;
      case 'LIVREE': return OrderStatus.livree;
      case 'ANNULEE': return OrderStatus.annulee;
      default: return OrderStatus.enAttente;
    }
  }

  static PaymentStatus _parsePaymentStatus(String status) {
    switch (status) {
      case 'PAYE': return PaymentStatus.paye;
      case 'PARTIEL': return PaymentStatus.partiel;
      default: return PaymentStatus.nonPaye;
    }
  }
}

class LigneCommande {
  final int? id;
  final int produitId;
  final Product? produitDetails;
  final int quantite;
  final double prixUnitaire;
  final double sousTotal;

  LigneCommande({
    this.id,
    required this.produitId,
    this.produitDetails,
    required this.quantite,
    required this.prixUnitaire,
    required this.sousTotal,
  });

  factory LigneCommande.fromJson(Map<String, dynamic> json) {
    return LigneCommande(
      id: json['id'],
      produitId: json['produit'],
      produitDetails: json['produit_details'] != null ? Product.fromJson(json['produit_details']) : null,
      quantite: json['quantite'],
      prixUnitaire: double.parse(json['prix_unitaire'].toString()),
      sousTotal: double.parse(json['sous_total'].toString()),
    );
  }
}

class PaymentRecord {
  final int id;
  final double montant;
  final DateTime date;
  final String mode;
  final String? reference;

  PaymentRecord({required this.id, required this.montant, required this.date, required this.mode, this.reference});

  factory PaymentRecord.fromJson(Map<String, dynamic> json) {
    return PaymentRecord(
      id: json['id'],
      montant: double.parse(json['montant'].toString()),
      date: DateTime.parse(json['date_paiement']),
      mode: json['mode_paiement'],
      reference: json['reference_transaction'],
    );
  }
}
