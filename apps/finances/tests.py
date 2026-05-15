"""
=============================================================================
 TESTS MODULE : FINANCES (Dépenses + Devises)

 Scénarios couverts :
  1. Dépense avec catégorie → enregistrée
  2. Dépense sans catégorie → refusée (400)
  3. Conversion devise USD → GNF automatique
  4. Devise GNF → pas de conversion
  5. Immutabilité : modification d'une dépense existante → refusée
=============================================================================
"""
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from django.contrib.auth import get_user_model
from .models import CategorieDepense, Depense

User = get_user_model()


# ─────────────────────────────────────────────
# 💸 TEST 9 : DÉPENSE
# ─────────────────────────────────────────────
class DepenseTestCase(APITestCase):
    """
    Catégorie : Transport
    Montant : 200 000 GNF
    → Enregistrée + visible dans stats
    """

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)
        self.categorie_transport = CategorieDepense.objects.create(nom="Transport")

    def test_depense_avec_categorie(self):
        """Dépense 200 000 GNF catégorie Transport → 201"""
        url = reverse("depenses-list")
        data = {
            "montant": 200000,
            "categorie": self.categorie_transport.id,
            "description": "Frais de déplacement Conakry",
        }
        res = self.client.post(url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["montant"], "200000.00")

    def test_depense_sans_categorie_refusee(self):
        """Dépense sans catégorie → refusée (400)"""
        url = reverse("depenses-list")
        data = {
            "montant": 100000,
            "description": "Achat sans catégorie",
        }
        res = self.client.post(url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_depense_enregistree_en_gnf_par_defaut(self):
        """Dépense en GNF → montant_gnf = montant"""
        url = reverse("depenses-list")
        data = {
            "montant": 500000,
            "categorie": self.categorie_transport.id,
            "description": "Location véhicule",
        }
        res = self.client.post(url, data, format="json")
        depense = Depense.objects.get(id=res.data["id"])
        self.assertEqual(depense.montant_gnf, 500000)


# ─────────────────────────────────────────────
# 💱 TEST 10 : DEVISE
# ─────────────────────────────────────────────
class DeviseTestCase(APITestCase):
    """
    Dépense : 50 USD × taux 8500
    → montant_gnf = 425 000 GNF
    """

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)
        self.categorie_achats = CategorieDepense.objects.create(
            nom="Achats Internationaux"
        )

    def test_conversion_usd_gnf(self):
        """50 USD × 8500 = 425 000 GNF"""
        url = reverse("depenses-list")
        data = {
            "montant": 50,
            "devise": "USD",
            "taux": 8500,
            "categorie": self.categorie_achats.id,
            "description": "Achat fournisseur Dubai",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        depense = Depense.objects.get(id=response.data["id"])
        self.assertEqual(depense.montant_gnf, 425000)

    def test_devise_gnf_pas_de_conversion(self):
        """Dépense GNF → taux = 1, montant_gnf = montant"""
        url = reverse("depenses-list")
        data = {
            "montant": 300000,
            "devise": "GNF",
            "categorie": self.categorie_achats.id,
            "description": "Frais locaux",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        depense = Depense.objects.get(id=response.data["id"])
        self.assertEqual(depense.montant_gnf, 300000)
        self.assertEqual(float(depense.taux), 1.0)


# ─────────────────────────────────────────────
# 🧠 TEST 13 : CAS D'ERREUR — DÉPENSE
# ─────────────────────────────────────────────
class DepenseErreurTestCase(APITestCase):
    """Cas limites pour les dépenses"""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)

    def test_depense_sans_description(self):
        """Dépense sans description → refusée ou champ vide"""
        url = reverse("depenses-list")
        data = {"montant": 100000}
        res = self.client.post(url, data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# 🔒 TEST IMMUTABILITÉ DÉPENSE (NOUVELLES RÈGLES ERP)
# ─────────────────────────────────────────────
class DepenseImmutabiliteTestCase(APITestCase):
    """Les dépenses ne peuvent PAS être modifiées ou supprimées via API."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            email="admin@test.com", nom="Admin BSG", password="password"
        )
        self.client.force_authenticate(user=self.user)
        self.categorie = CategorieDepense.objects.create(nom="Transport")

        # Créer une dépense
        url = reverse("depenses-list")
        res = self.client.post(url, {
            "montant": 200000,
            "categorie": self.categorie.id,
            "description": "Frais test",
        }, format="json")
        self.depense_id = res.data["id"]

    def test_modification_depense_bloquee_put(self):
        """PUT sur dépense → HTTP 405"""
        url = reverse("depenses-detail", args=[self.depense_id])
        res = self.client.put(url, {
            "montant": 100000,
            "categorie": self.categorie.id,
            "description": "Modifié",
        }, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_modification_depense_bloquee_patch(self):
        """PATCH sur dépense → HTTP 405"""
        url = reverse("depenses-detail", args=[self.depense_id])
        res = self.client.patch(url, {"montant": 999}, format="json")
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_suppression_depense_bloquee(self):
        """DELETE sur dépense → HTTP 405"""
        url = reverse("depenses-detail", args=[self.depense_id])
        res = self.client.delete(url)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

