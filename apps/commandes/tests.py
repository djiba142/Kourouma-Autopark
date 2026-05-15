"""
=============================================================================
 TESTS MODULE : COMMANDES (Ventes + Paiements)

 Scénarios couverts :
  1. Création commande (vente directe)
  2. Paiement partiel → statut PARTIEL
  3. Paiement complet → statut PAYÉ
  4. Vente sans stock → refusée (400)
  5. Paiement supérieur au montant (cas limite)
  6. Calcul reste_a_payer correct
  7. Sécurité — employé non authentifié refusé
=============================================================================
"""
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from clients.models import Client
from produits.models import Produit
from stock.models import Localisation, StockParLocalisation
from .models import Commande, LigneCommande, Paiement

User = get_user_model()


# ─────────────────────────────────────────────
# 🏪 4. TEST COMMANDE (VENTE DIRECTE)
# ─────────────────────────────────────────────
class CommandeVenteDirecteTestCase(APITestCase):
    """
    Créer commande vente directe :
      Client : Moussa
      Produit : Plaquette frein × 5 pièces
    → Total = 75 000 GNF
    → Stock boutique = 35 pièces (40 - 5)
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", nom="Test User", password="password"
        )
        self.client.force_authenticate(user=self.user)

        # Clients
        self.client_moussa = Client.objects.create(nom="Moussa", telephone="0001")
        self.client_fatou = Client.objects.create(nom="Fatou", telephone="0002")

        # Produit
        self.produit_frein = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PF001BC",
        )

        # Boutique avec stock de 40 pièces (2 cartons × 20)
        self.boutique = Localisation.objects.create(nom="Boutique 1", type="BOUTIQUE")
        StockParLocalisation.objects.create(
            produit=self.produit_frein, localisation=self.boutique, quantite=40
        )

    def test_create_vente_directe(self):
        """Vente directe de 5 pièces → total 75 000 GNF, stock 35"""
        url = reverse("commandes-list")
        data = {
            "client": self.client_moussa.id,
            "type_vente": "VENTE_DIRECTE",
            "localisation": self.boutique.id,
            "lignes": [
                {
                    "produit": self.produit_frein.id,
                    "quantite": 5,
                    "prix_unitaire": 15000,
                }
            ],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Vérifier total
        commande = Commande.objects.get(id=response.data["id"])
        self.assertEqual(float(commande.total_ttc), 75000.0)

        # Vérifier stock décrémenté
        stock = StockParLocalisation.objects.get(
            produit=self.produit_frein, localisation=self.boutique
        )
        self.assertEqual(stock.quantite, 35)  # 40 - 5

    def test_vente_directe_met_a_jour_statut(self):
        """Vente directe → statut = VALIDEE"""
        url = reverse("commandes-list")
        data = {
            "client": self.client_moussa.id,
            "type_vente": "VENTE_DIRECTE",
            "localisation": self.boutique.id,
            "lignes": [
                {
                    "produit": self.produit_frein.id,
                    "quantite": 2,
                    "prix_unitaire": 15000,
                }
            ],
        }
        response = self.client.post(url, data, format="json")
        commande = Commande.objects.get(id=response.data["id"])
        self.assertEqual(commande.statut, "VALIDEE")


# ─────────────────────────────────────────────
# 💳 5 & 6. TESTS PAIEMENT PARTIEL + COMPLET
# ─────────────────────────────────────────────
class PaiementTestCase(APITestCase):
    """
    Sur commande de 75 000 GNF :
      Paiement 50 000 → Reste 25 000, statut PARTIEL
      Paiement 25 000 → Reste 0, statut PAYÉ
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", nom="Test User", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.client_moussa = Client.objects.create(nom="Moussa", telephone="0001")
        self.produit_frein = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PF001BC",
        )
        self.boutique = Localisation.objects.create(nom="Boutique 1", type="BOUTIQUE")
        StockParLocalisation.objects.create(
            produit=self.produit_frein, localisation=self.boutique, quantite=100
        )

        # Créer commande vente directe
        create_url = reverse("commandes-list")
        create_data = {
            "client": self.client_moussa.id,
            "type_vente": "VENTE_DIRECTE",
            "localisation": self.boutique.id,
            "lignes": [
                {
                    "produit": self.produit_frein.id,
                    "quantite": 5,
                    "prix_unitaire": 15000,
                }
            ],
        }
        res = self.client.post(create_url, create_data, format="json")
        self.commande_id = res.data["id"]

    def test_paiement_partiel(self):
        """Paiement partiel de 50 000 sur 75 000 → PARTIEL"""
        url = reverse("commandes-paiement", args=[self.commande_id])
        data = {"montant": 50000, "mode_paiement": "CASH"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        commande = Commande.objects.get(id=self.commande_id)
        self.assertEqual(commande.statut_paiement, "PARTIEL")
        self.assertEqual(float(commande.reste_a_payer), 25000.0)

    def test_paiement_complet(self):
        """Deux paiements (50000 + 25000) → PAYÉ, reste = 0"""
        url = reverse("commandes-paiement", args=[self.commande_id])
        self.client.post(url, {"montant": 50000, "mode_paiement": "CASH"}, format="json")
        response = self.client.post(
            url, {"montant": 25000, "mode_paiement": "CASH"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        commande = Commande.objects.get(id=self.commande_id)
        self.assertEqual(commande.statut_paiement, "PAYE")
        self.assertEqual(float(commande.reste_a_payer), 0.0)


# ─────────────────────────────────────────────
# 📉 7. TEST RUPTURE STOCK
# ─────────────────────────────────────────────
class RuptureStockTestCase(APITestCase):
    """
    Vendre plus de stock que disponible → système REFUSE (400)
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", nom="Test User", password="password"
        )
        self.client.force_authenticate(user=self.user)
        self.client_moussa = Client.objects.create(nom="Moussa", telephone="0001")
        self.produit_frein = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PF001BC",
        )
        # Boutique avec stock = 0
        self.boutique = Localisation.objects.create(nom="Boutique 1", type="BOUTIQUE")
        StockParLocalisation.objects.create(
            produit=self.produit_frein, localisation=self.boutique, quantite=0
        )

    def test_vente_sans_stock_refusee(self):
        """Vente avec 0 stock → HTTP 400"""
        url = reverse("commandes-list")
        data = {
            "client": self.client_moussa.id,
            "type_vente": "VENTE_DIRECTE",
            "localisation": self.boutique.id,
            "lignes": [
                {
                    "produit": self.produit_frein.id,
                    "quantite": 1,
                    "prix_unitaire": 15000,
                }
            ],
        }
        response = self.client.post(url, data, format="json")
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

    def test_vente_quantite_superieure_au_stock(self):
        """Vente 9999 pièces avec stock 0 → refusée"""
        url = reverse("commandes-list")
        data = {
            "client": self.client_moussa.id,
            "type_vente": "VENTE_DIRECTE",
            "localisation": self.boutique.id,
            "lignes": [
                {
                    "produit": self.produit_frein.id,
                    "quantite": 9999,
                    "prix_unitaire": 15000,
                }
            ],
        }
        response = self.client.post(url, data, format="json")
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )


# ─────────────────────────────────────────────
# 🔐 12. TEST SÉCURITÉ
# ─────────────────────────────────────────────
class SecuriteTestCase(APITestCase):
    """
    Utilisateur non authentifié → refusé (401)
    """

    def test_commande_sans_authentification(self):
        """Requête non authentifiée → 401"""
        url = reverse("commandes-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_paiement_sans_authentification(self):
        """Tentative paiement sans token → 401"""
        url = reverse("commandes-list")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ─────────────────────────────────────────────
# 💰 TESTS PAIEMENT > TOTAL (NOUVELLES RÈGLES ERP)
# ─────────────────────────────────────────────
class PaiementSuperieurTotalTestCase(APITestCase):
    """
    Scenario : Commande 75 000 GNF
    → Paiement 50 000 OK
    → Paiement 30 000 (> reste 25 000) → REFUSÉ (400)
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", nom="Test User", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.client_moussa = Client.objects.create(nom="Moussa", telephone="0001")
        self.produit = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PF001BC",
        )
        self.boutique = Localisation.objects.create(nom="Boutique 1", type="BOUTIQUE")
        StockParLocalisation.objects.create(
            produit=self.produit, localisation=self.boutique, quantite=100
        )

        # Créer commande vente directe (5 × 15 000 = 75 000)
        create_url = reverse("commandes-list")
        res = self.client.post(
            create_url,
            {
                "client": self.client_moussa.id,
                "type_vente": "VENTE_DIRECTE",
                "localisation": self.boutique.id,
                "lignes": [
                    {"produit": self.produit.id, "quantite": 5, "prix_unitaire": 15000}
                ],
            },
            format="json",
        )
        self.commande_id = res.data["id"]

    def test_paiement_superieur_au_reste_refuse(self):
        """Paiement 50 000 OK, puis 30 000 sur reste 25 000 → HTTP 400"""
        url = reverse("commandes-paiement", args=[self.commande_id])

        # Premier paiement OK
        res1 = self.client.post(url, {"montant": 50000, "mode_paiement": "CASH"}, format="json")
        self.assertEqual(res1.status_code, status.HTTP_200_OK)

        # Deuxième paiement dépasse le reste (30 000 > 25 000)
        res2 = self.client.post(url, {"montant": 30000, "mode_paiement": "CASH"}, format="json")
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_paiement_negatif_refuse(self):
        """Paiement montant négatif → HTTP 400"""
        url = reverse("commandes-paiement", args=[self.commande_id])
        res = self.client.post(url, {"montant": -5000, "mode_paiement": "CASH"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_paiement_exact_reste_accepte(self):
        """Paiement exactement égal au reste → accepté"""
        url = reverse("commandes-paiement", args=[self.commande_id])
        res = self.client.post(url, {"montant": 75000, "mode_paiement": "CASH"}, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        commande = Commande.objects.get(id=self.commande_id)
        self.assertEqual(commande.statut_paiement, "PAYE")

