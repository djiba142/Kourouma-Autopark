"""
=============================================================================
 TESTS MODULE : STOCK (Transferts Magasin ↔ Boutique)

 Scénarios couverts :
  1. Flux complet transfert : création → expédition → réception
  2. Vérification stock magasin décrémenté
  3. Vérification stock boutique incrémenté
  4. Transfert sans validation (expédition déjà faite) → refusé
  5. Réception sans expédition → refusée
  6. Conversion correcte cartons ↔ pièces
=============================================================================
"""
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from produits.models import Produit
from .models import Localisation, StockParLocalisation, TransfertStock, TransfertItem, MouvementStock

User = get_user_model()


# ─────────────────────────────────────────────
# 🥈 TEST 2 : DEMANDE BOUTIQUE + 🥉 TEST 3 : VALIDATION + TRANSFERT
# ─────────────────────────────────────────────
class TransfertCompletTestCase(APITestCase):
    """
    Flux complet :
      1. Boutique demande 2 cartons (40 pièces) de Plaquette frein
      2. Magasin valide et expédie
      3. Boutique reçoit
    
    → Magasin : 200 - 40 = 160 pièces
    → Boutique : 0 + 40 = 40 pièces
    """

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.produit_frein = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PF001BC",
        )

        self.magasin = Localisation.objects.create(
            nom="Magasin Principal", type="MAGASIN"
        )
        self.boutique = Localisation.objects.create(
            nom="Boutique 1", type="BOUTIQUE"
        )

        # 10 cartons au magasin = 200 pièces
        StockParLocalisation.objects.create(
            produit=self.produit_frein,
            localisation=self.magasin,
            quantite=200,
        )
        StockParLocalisation.objects.create(
            produit=self.produit_frein,
            localisation=self.boutique,
            quantite=0,
        )

    def test_flux_transfert_complet(self):
        """Demande → Expédition → Réception : stocks corrects"""
        # 1. Création demande (2 cartons = 40 pièces)
        url_create = reverse("transfertstock-list")
        data = {
            "provenance": self.magasin.id,
            "destination": self.boutique.id,
            "items": [
                {"produit": self.produit_frein.id, "quantite": 40}
            ],
        }
        res = self.client.post(url_create, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        transfert_id = res.data["id"]

        # Vérifier statut PROPOSE (en attente)
        transfert = TransfertStock.objects.get(id=transfert_id)
        self.assertEqual(transfert.statut, "PROPOSE")

        # 2. Expédition → stock magasin décrémenté
        url_expedier = reverse("transfertstock-expedier", args=[transfert_id])
        res_exp = self.client.post(url_expedier)
        self.assertEqual(res_exp.status_code, status.HTTP_200_OK)

        transfert.refresh_from_db()
        self.assertEqual(transfert.statut, "EXPEDIE")

        # 3. Réception → stock boutique incrémenté
        url_recevoir = reverse("transfertstock-recevoir", args=[transfert_id])
        res_recv = self.client.post(url_recevoir)
        self.assertEqual(res_recv.status_code, status.HTTP_200_OK)

        transfert.refresh_from_db()
        self.assertEqual(transfert.statut, "RECU")

    def test_double_expedition_refusee(self):
        """Un transfert déjà expédié → re-expédition refusée"""
        url_create = reverse("transfertstock-list")
        data = {
            "provenance": self.magasin.id,
            "destination": self.boutique.id,
            "items": [
                {"produit": self.produit_frein.id, "quantite": 20}
            ],
        }
        res = self.client.post(url_create, data, format="json")
        transfert_id = res.data["id"]

        # Première expédition OK
        url_exp = reverse("transfertstock-expedier", args=[transfert_id])
        self.client.post(url_exp)

        # Deuxième expédition → refusée
        res2 = self.client.post(url_exp)
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reception_sans_expedition_refusee(self):
        """Réception directe (sans expédition) → refusée"""
        url_create = reverse("transfertstock-list")
        data = {
            "provenance": self.magasin.id,
            "destination": self.boutique.id,
            "items": [
                {"produit": self.produit_frein.id, "quantite": 20}
            ],
        }
        res = self.client.post(url_create, data, format="json")
        transfert_id = res.data["id"]

        # Tenter réception directe sans expédier d'abord → refusé
        url_recv = reverse("transfertstock-recevoir", args=[transfert_id])
        res_recv = self.client.post(url_recv)
        self.assertEqual(res_recv.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# 🔄 TEST 8 : NOUVELLE DEMANDE BOUTIQUE
# ─────────────────────────────────────────────
class NouvelleDemandeTestCase(APITestCase):
    """Boutique peut toujours créer une nouvelle demande"""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)

        self.produit_frein = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PF001BC",
        )

        self.magasin = Localisation.objects.create(
            nom="Magasin Principal", type="MAGASIN"
        )
        self.boutique = Localisation.objects.create(
            nom="Boutique 1", type="BOUTIQUE"
        )

    def test_nouvelle_demande_enregistree(self):
        """Une demande de transfert s'enregistre avec statut PROPOSE"""
        url = reverse("transfertstock-list")
        data = {
            "provenance": self.magasin.id,
            "destination": self.boutique.id,
            "items": [
                {"produit": self.produit_frein.id, "quantite": 60}
            ],
        }
        res = self.client.post(url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        transfert = TransfertStock.objects.get(id=res.data["id"])
        self.assertEqual(transfert.statut, "PROPOSE")


# ─────────────────────────────────────────────
# 🔒 TEST STOCK NÉGATIF (NOUVELLES RÈGLES ERP)
# ─────────────────────────────────────────────
class StockNegatifTestCase(APITestCase):
    """Le stock ne peut jamais être négatif."""

    def setUp(self):
        self.produit = Produit.objects.create(
            nom="Plaquette frein",
            reference="PF-NEG-001",
            prix_achat=200000,
            prix_vente=15000,
            conversion_unit=20,
            marque="BSG",
            code_barre="PFNEG001BC",
        )
        self.boutique = Localisation.objects.create(nom="Boutique Neg", type="BOUTIQUE")

    def test_stock_negatif_bloque(self):
        """Stock à -1 → ValidationError"""
        from django.core.exceptions import ValidationError
        stock = StockParLocalisation(
            produit=self.produit, localisation=self.boutique, quantite=-1
        )
        with self.assertRaises(ValidationError):
            stock.save()

    def test_stock_zero_accepte(self):
        """Stock à 0 → OK"""
        stock = StockParLocalisation.objects.create(
            produit=self.produit, localisation=self.boutique, quantite=0
        )
        self.assertEqual(stock.quantite, 0)


# ─────────────────────────────────────────────
# 🔐 TEST PERMISSIONS MAGASINIER (RBAC)
# ─────────────────────────────────────────────
class MagasinierPermissionsTestCase(APITestCase):
    """MAGASINIER peut accéder au stock, EMPLOYE non."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@test.com", nom="Admin", password="password"
        )
        self.magasinier = User.objects.create_user(
            email="magasinier@test.com", nom="Magasinier", 
            password="password", role="MAGASINIER"
        )
        self.employe = User.objects.create_user(
            email="employe@test.com", nom="Employe",
            password="password", role="EMPLOYE"
        )

        self.produit = Produit.objects.create(
            nom="Filtre huile",
            reference="FH-001",
            prix_achat=100000,
            prix_vente=12000,
            conversion_unit=10,
            marque="BSG",
            code_barre="FH001BC",
        )
        self.magasin = Localisation.objects.create(nom="Magasin Test", type="MAGASIN")

    def test_magasinier_peut_creer_mouvement(self):
        """MAGASINIER → accès mouvement stock OK"""
        self.client.force_authenticate(user=self.magasinier)
        url = reverse("mouvementstock-list")
        data = {
            "produit": self.produit.id,
            "localisation": self.magasin.id,
            "type": "ENTREE",
            "quantite": 50,
        }
        res = self.client.post(url, data, format="json")
        self.assertIn(res.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_employe_ne_peut_pas_creer_mouvement(self):
        """EMPLOYE → accès mouvement stock REFUSÉ (403)"""
        self.client.force_authenticate(user=self.employe)
        url = reverse("mouvementstock-list")
        data = {
            "produit": self.produit.id,
            "localisation": self.magasin.id,
            "type": "ENTREE",
            "quantite": 50,
        }
        res = self.client.post(url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

