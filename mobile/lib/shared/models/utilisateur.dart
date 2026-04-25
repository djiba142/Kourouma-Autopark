import 'package:equatable/equatable.dart';

class Utilisateur extends Equatable {
  final int id;
  final String email;
  final String nom;
  final String role;
  final bool? actif;
  final String? fcmToken;
  final DateTime? dateCreation;

  const Utilisateur({
    required this.id,
    required this.email,
    required this.nom,
    required this.role,
    this.actif,
    this.fcmToken,
    this.dateCreation,
  });

  bool get isAdmin => role == 'ADMIN';
  bool get isEmploye => role == 'EMPLOYE';

  factory Utilisateur.fromJson(Map<String, dynamic> json) {
    return Utilisateur(
      id: json['id'],
      email: json['email'],
      nom: json['nom'],
      role: json['role'],
      actif: json['actif'],
      fcmToken: json['fcm_token'],
      dateCreation: json['date_creation'] != null 
          ? DateTime.parse(json['date_creation']) 
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'nom': nom,
      'role': role,
      'actif': actif,
      'fcm_token': fcmToken,
      'date_creation': dateCreation?.toIso8601String(),
    };
  }

  @override
  List<Object?> get props => [id, email, nom, role, actif, fcmToken, dateCreation];
}
