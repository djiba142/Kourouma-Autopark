import 'package:equatable/equatable.dart';

class Produit extends Equatable {
  final int id;
  final String nom;
  final String reference;
  final String categorie;
  final String marque;
  final double prixVente;
  final double? prixAchat; // Masked for employees
  final int quantite;
  final int seuilAlerte;
  final String? codeBarre;
  final String? imageUrl;

  const Produit({
    required this.id,
    required this.nom,
    required this.reference,
    required this.categorie,
    required this.marque,
    required this.prixVente,
    this.prixAchat,
    required this.quantite,
    required this.seuilAlerte,
    this.codeBarre,
    this.imageUrl,
  });

  bool get estEnAlerte => quantite <= seuilAlerte;

  factory Produit.fromJson(Map<String, dynamic> json) {
    return Produit(
      id: json['id'],
      nom: json['nom'],
      reference: json['reference'],
      categorie: json['categorie_nom'] ?? 'Général',
      marque: json['marque'],
      prixVente: (json['prix_vente'] as num).toDouble(),
      prixAchat: (json['prix_achat'] as num?)?.toDouble(),
      quantite: json['quantite'],
      seuilAlerte: json['seuil_alerte'],
      codeBarre: json['code_barre'],
      imageUrl: json['image_url'],
    );
  }

  @override
  List<Object?> get props => [id, nom, reference, categorie, marque, prixVente, prixAchat, quantite, seuilAlerte, codeBarre, imageUrl];
}
