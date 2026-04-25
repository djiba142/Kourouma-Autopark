import 'package:equatable/equatable.dart';

class Client extends Equatable {
  final int id;
  final String nom;
  final String telephone;
  final String? email;
  final String? adresse;
  final double limiteCredit;
  final String scoreStatut;
  final double totalDette;
  final double totalPaye;
  final double totalAchats;
  final bool alerteCredit;
  final bool actif;

  const Client({
    required this.id,
    required this.nom,
    required this.telephone,
    this.email,
    this.adresse,
    required this.limiteCredit,
    required this.scoreStatut,
    required this.totalDette,
    required this.totalPaye,
    required this.totalAchats,
    required this.alerteCredit,
    required this.actif,
  });

  factory Client.fromJson(Map<String, dynamic> json) {
    return Client(
      id: json['id'],
      nom: json['nom'],
      telephone: json['telephone'],
      email: json['email'],
      adresse: json['adresse'],
      limiteCredit: double.parse(json['limite_credit'].toString()),
      scoreStatut: json['score_statut'],
      totalDette: double.parse(json['total_dette'].toString()),
      totalPaye: double.parse(json['total_paye'].toString()),
      totalAchats: double.parse(json['total_achats'].toString()),
      alerteCredit: json['alerte_credit'],
      actif: json['actif'],
    );
  }

  @override
  List<Object?> get props => [id, nom, telephone, alerteCredit];
}
