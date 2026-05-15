"""
=============================================================================
 TESTS MODULE : ACHATS (Commandes d'Achat fournisseur)
 
 Scénarios couverts :
  1. Création PO (Purchase Order) fournisseur
  2. Réception marchandise → stock magasin augmenté
  3. Double réception refusée
  4. Conversion cartons → pièces correcte
=============================================================================
"""
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from produits.models import Produit
from stock.models import Localisation, StockParLocalisation, MouvementStock
from .models import Fournisseur, CommandeAchat, LigneAchat
from datetime import date

User = get_user_model()


class AchatFournisseurTestCase(APITestCase):
    """
    🥇 TEST 1 : ACHAT FOURNISSEUR
    Créer un achat de 10 cartons de plaquettes frein
    → Stock magasin doit être mis à jour après réception
    """

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)

        # Produit : Plaquette frein — 1 carton = 20 pièces
        self.produit_frein = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PF001BARCODE",
        )

        # Produit : Filtre huile — 1 carton = 10 pièces
        self.produit_filtre = Produit.objects.create(
            nom="Filtre huile",
            reference="FH-001",
            prix_achat=100000,
            prix_vente=12000,
            conversion_unit=10,
            marque="BSG",
            code_barre="FH001BARCODE",
        )

        # Magasin principal (stock de destination)
        self.magasin = Localisation.objects.create(
            nom="Magasin Principal", type="MAGASIN"
        )

        # Fournisseur
        self.fournisseur = Fournisseur.objects.create(
            nom="Dubai Auto Parts",
            pays="Émirats Arabes Unis",
            type="INTERNATIONAL",
            devise_par_defaut="USD",
        )

    def test_creation_achat_fournisseur(self):
        """Créer un PO avec 10 cartons de plaquettes frein"""
        url = reverse("achats-list")
        data = {
            "fournisseur": self.fournisseur.id,
            "devise": "USD",
            "taux_change": 8500,
            "date_commande": str(date.today()),
            "lignes": [
                {
                    "produit": self.produit_frein.id,
                    "quantite_cartons": 10,
                    "prix_unitaire_devise": 200,
                }
            ],
        }
        response = self.client.post(url, data, format="json")
        if response.status_code == 400:
            print(f"DEBUG ACHATS 400: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        po = CommandeAchat.objects.get(id=response.data["id"])
        self.assertEqual(po.statut, "BROUILLON")

    def test_reception_augmente_stock_magasin(self):
        """
        Après réception :
        - 10 cartons × 20 pièces = 200 pièces ajoutées au magasin
        - Mouvement ENTREE créé
        """
        # Créer le PO manuellement
        po = CommandeAchat.objects.create(
            reference="PO-TEST-001",
            fournisseur=self.fournisseur,
            devise="USD",
            taux_change=8500,
            date_commande=date.today(),
            cree_par=self.user,
        )
        LigneAchat.objects.create(
            achat=po,
            produit=self.produit_frein,
            quantite_cartons=10,
            prix_unitaire_devise=200,
        )

        # Réceptionner
        url = reverse("achats-recevoir", args=[po.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Vérifier stock magasin → 10 × 20 = 200 pièces
        stock = StockParLocalisation.objects.get(
            produit=self.produit_frein, localisation=self.magasin
        )
        self.assertEqual(stock.quantite, 200)

        # Vérifier mouvement
        mouvement = MouvementStock.objects.filter(
            produit=self.produit_frein, type="ENTREE"
        ).first()
        self.assertIsNotNone(mouvement)
        self.assertEqual(mouvement.quantite, 200)

        # Vérifier statut PO
        po.refresh_from_db()
        self.assertEqual(po.statut, "RECUE")

    def test_double_reception_refusee(self):
        """Un PO déjà reçu ne peut pas être reçu une 2ème fois"""
        po = CommandeAchat.objects.create(
            reference="PO-TEST-002",
            fournisseur=self.fournisseur,
            devise="USD",
            taux_change=8500,
            date_commande=date.today(),
            statut="RECUE",
            cree_par=self.user,
        )
        url = reverse("achats-recevoir", args=[po.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_conversion_cartons_pieces(self):
        """La conversion pièces = cartons × conversion_unit doit être exacte"""
        po = CommandeAchat.objects.create(
            reference="PO-TEST-003",
            fournisseur=self.fournisseur,
            devise="USD",
            taux_change=8500,
            date_commande=date.today(),
            cree_par=self.user,
        )
        ligne = LigneAchat.objects.create(
            achat=po,
            produit=self.produit_filtre,
            quantite_cartons=5,
            prix_unitaire_devise=100,
        )
        # 5 cartons × 10 pièces/carton = 50 pièces
        self.assertEqual(ligne.quantite_pieces, 50)

    def test_calculs_financiers_achat(self):
        """Vérifier sous_total_devise et sous_total_gnf"""
        po = CommandeAchat.objects.create(
            reference="PO-TEST-004",
            fournisseur=self.fournisseur,
            devise="USD",
            taux_change=8500,
            date_commande=date.today(),
            cree_par=self.user,
        )
        ligne = LigneAchat.objects.create(
            achat=po,
            produit=self.produit_frein,
            quantite_cartons=10,
            prix_unitaire_devise=200,
        )
        # sous_total_devise = 10 × 200 = 2000 USD
        self.assertEqual(ligne.sous_total_devise, 2000)
        # sous_total_gnf = 2000 × 8500 = 17 000 000 GNF
        self.assertEqual(ligne.sous_total_gnf, 17_000_000)
