import 'package:equatable/equatable.dart';

enum TypeDepense { entreprise, personnel }
enum Periodicite { jour, semaine, mois, an }
enum Devise { gnf, usd }

class Depense extends Equatable {
  final int id;
  final double montant;
  final Devise devise;
  final double taux;
  final double montantGnf;
  final String description;
  final int? categorieId;
  final String? categorieNom;
  final TypeDepense type;
  final Periodicite periodicite;
  final DateTime date;
  final String? preuveUrl;
  final String? creeParNom;

  const Depense({
    required this.id,
    required this.montant,
    required this.devise,
    required this.taux,
    required this.montantGnf,
    required this.description,
    this.categorieId,
    this.categorieNom,
    required this.type,
    required this.periodicite,
    required this.date,
    this.preuveUrl,
    this.creeParNom,
  });

  factory Depense.fromJson(Map<String, dynamic> json) {
    return Depense(
      id: json['id'],
      montant: (json['montant'] as num).toDouble(),
      devise: json['devise'] == 'USD' ? Devise.usd : Devise.gnf,
      taux: (json['taux'] as num).toDouble(),
      montantGnf: (json['montant_gnf'] as num).toDouble(),
      description: json['description'],
      categorieId: json['categorie'],
      categorieNom: json['categorie_nom'],
      type: json['type_depense'] == 'ENTREPRISE' 
          ? TypeDepense.entreprise 
          : TypeDepense.personnel,
      periodicite: _parsePeriodicite(json['periodicite']),
      date: DateTime.parse(json['date_depense']),
      preuveUrl: json['preuve'],
      creeParNom: json['cree_par_nom'],
    );
  }

  static Periodicite _parsePeriodicite(String? value) {
    switch (value) {
      case 'SEMAINE': return Periodicite.semaine;
      case 'MOIS': return Periodicite.mois;
      case 'AN': return Periodicite.an;
      default: return Periodicite.jour;
    }
  }

  @override
  List<Object?> get props => [
    id, montant, devise, taux, montantGnf, 
    description, type, periodicite, date, preuveUrl
  ];
}
