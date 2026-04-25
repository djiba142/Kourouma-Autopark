"""
=============================================================================
 TESTS MODULE : DASHBOARD (Finance Central)

 Scénarios couverts :
  1. Dashboard retourne données correctes
  2. Dashboard accessible authentifié
  3. Dashboard refusé sans authentification
=============================================================================
"""
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from clients.models import Client
from produits.models import Produit
from stock.models import Localisation, StockParLocalisation
from commandes.models import Commande, LigneCommande
from finances.models import CategorieDepense, Depense

User = get_user_model()


class DashboardTestCase(APITestCase):
    """Dashboard Finance Central retourne les bonnes données."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)

        # Données de base
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
            produit=self.produit, localisation=self.boutique, quantite=50
        )

    def test_dashboard_retourne_donnees_correctes(self):
        """GET dashboard → données finance présentes"""
        url = reverse("dashboard")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        data = res.data
        self.assertIn("total_ventes", data)
        self.assertIn("total_depenses", data)
        self.assertIn("profit", data)
        self.assertIn("stock_global", data)
        self.assertIn("dettes_clients", data)
        self.assertIn("top_produits", data)
        self.assertIn("dernieres_commandes", data)
        self.assertIn("nb_commandes_en_cours", data)
        self.assertIn("nb_produits_alerte", data)

    def test_dashboard_stock_global(self):
        """Stock global = somme des quantités par localisation"""
        url = reverse("dashboard")
        res = self.client.get(url)
        self.assertEqual(res.data["stock_global"], 50)

    def test_dashboard_sans_authentification_refuse(self):
        """Dashboard sans token → 401"""
        self.client.force_authenticate(user=None)
        url = reverse("dashboard")
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
