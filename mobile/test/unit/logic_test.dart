import 'package:flutter_test/flutter_test.dart';
import 'package:autopieces_pro/features/commandes/data/models/ligne_panier.dart';
import 'package:autopieces_pro/shared/models/produit.dart';

void main() {
  group('LignePanier Tests', () {
    const testProduit = Produit(
      id: 1,
      nom: 'Plaquette frein',
      reference: 'REF-001',
      categorie: 'Moteur',
      marque: 'Toyota',
      prixVente: 15000.0,
      quantite: 100,
      seuilAlerte: 10,
    );

    test('Le sous-total doit être correct (prix * quantite)', () {
      final ligne = LignePanier(produit: testProduit, quantite: 3);
      expect(ligne.sousTotal, 45000.0);
    });

    test('Le sous-total doit se mettre à jour quand la quantité change', () {
      final ligne = LignePanier(produit: testProduit, quantite: 1);
      expect(ligne.sousTotal, 15000.0);

      ligne.quantite = 5;
      expect(ligne.sousTotal, 75000.0);
    });

    test('Le statut d\'alerte stock du produit doit fonctionner', () {
      const pAlerte = Produit(
        id: 2,
        nom: 'Filtre huile',
        reference: 'REF-002',
        categorie: 'Moteur',
        marque: 'Bosch',
        prixVente: 12000.0,
        quantite: 5,
        seuilAlerte: 10,
      );
      expect(pAlerte.estEnAlerte, true);
    });
  });
}
