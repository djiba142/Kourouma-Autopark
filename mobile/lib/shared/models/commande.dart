import 'package:equatable/equatable.dart';
import 'client.dart';

enum StatutCommande {
  enAttente, validee, enPreparation, prete, expediee, livree, annulee
}

enum StatutPaiement {
  nonPaye, partiel, paye
}

class Commande extends Equatable {
  final int id;
  final String numero;
  final Client? client;
  final StatutCommande statut;
  final StatutPaiement statutPaiement;
  final double totalTtc;
  final double remise;
  final double? resteAPayer;
  final String typeVente;
  final DateTime dateCreation;

  const Commande({
    required this.id,
    required this.numero,
    this.client,
    required this.statut,
    required this.statutPaiement,
    required this.totalTtc,
    required this.remise,
    this.resteAPayer,
    required this.typeVente,
    required this.dateCreation,
  });

  // Helpers
  bool get estEntierementPayee => statutPaiement == StatutPaiement.paye;
  bool get aUneDette => statutPaiement != StatutPaiement.paye;

  factory Commande.fromJson(Map<String, dynamic> json) {
    return Commande(
      id: json['id'],
      numero: json['numero'],
      client: json['client'] != null ? Client.fromJson(json['client']) : null,
      statut: _parseStatut(json['statut']),
      statutPaiement: _parseStatutPaiement(json['statut_paiement']),
      totalTtc: (json['total_ttc'] as num).toDouble(),
      remise: (json['remise'] as num).toDouble(),
      resteAPayer: (json['reste_a_payer'] as num?)?.toDouble(),
      typeVente: json['type_vente'],
      dateCreation: DateTime.parse(json['date_creation']),
    );
  }

  static StatutCommande _parseStatut(String value) {
    switch (value) {
      case 'EN_ATTENTE': return StatutCommande.enAttente;
      case 'VALIDEE': return StatutCommande.validee;
      case 'EN_PREPARATION': return StatutCommande.enPreparation;
      case 'PRETE': return StatutCommande.prete;
      case 'EXPEDIEE': return StatutCommande.expediee;
      case 'LIVREE': return StatutCommande.livree;
      case 'ANNULEE': return StatutCommande.annulee;
      default: return StatutCommande.enAttente;
    }
  }

  static StatutPaiement _parseStatutPaiement(String value) {
    switch (value) {
      case 'NON_PAYE': return StatutPaiement.nonPaye;
      case 'PARTIEL': return StatutPaiement.partiel;
      case 'PAYE': return StatutPaiement.paye;
      default: return StatutPaiement.nonPaye;
    }
  }

  @override
  List<Object?> get props => [id, numero, client, statut, statutPaiement, totalTtc, remise, resteAPayer, typeVente, dateCreation];
}
