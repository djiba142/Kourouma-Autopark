import 'package:equatable/equatable.dart';

class Client extends Equatable {
  final int id;
  final String nom;
  final String telephone;
  final String? email;
  final String? adresse;
  final double limiteCredit;
  final double totalDette;
  final String scoreStatut;
  final bool actif;

  const Client({
    required this.id,
    required this.nom,
    required this.telephone,
    this.email,
    this.adresse,
    this.limiteCredit = 0.0,
    this.totalDette = 0.0,
    this.scoreStatut = 'BON',
    this.actif = true,
  });

  bool get isOverLimit => totalDette > limiteCredit && limiteCredit > 0;

  factory Client.fromJson(Map<String, dynamic> json) {
    return Client(
      id: json['id'],
      nom: json['nom'],
      telephone: json['telephone'],
      email: json['email'],
      adresse: json['adresse'],
      limiteCredit: (json['limite_credit'] as num?)?.toDouble() ?? 0.0,
      totalDette: (json['total_dette'] as num?)?.toDouble() ?? 0.0,
      scoreStatut: json['score_statut'] ?? 'BON',
      actif: json['actif'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'nom': nom,
      'telephone': telephone,
      'email': email,
      'adresse': adresse,
      'limite_credit': limiteCredit,
      'total_dette': totalDette,
      'score_statut': scoreStatut,
      'actif': actif,
    };
  }

  @override
  List<Object?> get props => [id, nom, telephone, email, adresse, limiteCredit, totalDette, scoreStatut, actif];
}
