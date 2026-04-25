from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from .models import Utilisateur

class AuthTestCase(APITestCase):
    def setUp(self):
        self.user = Utilisateur.objects.create_user(
            email='admin@bsg.com', 
            nom='Admin BSG', 
            password='1234',
            role='ADMIN'
        )
        self.login_url = reverse('login')

    def test_login_jwt(self):
        """Test que le login retourne des tokens JWT valides."""
        data = {"email": "admin@bsg.com", "password": "1234"}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

class ProtectedTestCase(APITestCase):
    def test_access_without_token(self):
        """Test que les accès non-authentifiés sont bloqués (401)."""
        url = reverse('commandes-list')
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class RoleTestCase(APITestCase):
    def setUp(self):
        self.admin = Utilisateur.objects.create_user(
            email='admin@bsg.com', nom='Admin', password='1234', role='ADMIN'
        )
        self.employe = Utilisateur.objects.create_user(
            email='emp@bsg.com', nom='Employe', password='1234', role='EMPLOYE'
        )
        # DefaultRouter uses the model name lowercase if no basename is specified
        self.url_stock = reverse('mouvementstock-list')

    def test_employe_ne_peut_pas_ajouter_stock(self):
        """Test qu'un employé reçoit un 403 Forbidden sur une route Admin."""
        # Login pour obtenir le token
        login_res = self.client.post(reverse('login'), {"email": "emp@bsg.com", "password": "1234"})
        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post(self.url_stock, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_peut_ajouter_stock(self):
        """Test qu'un admin a accès à la route (pas de 403)."""
        login_res = self.client.post(reverse('login'), {"email": "admin@bsg.com", "password": "1234"})
        token = login_res.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        response = self.client.post(self.url_stock, {})
        # On ne s'attend pas à un 403 (peut être 400 si données vides, mais pas 403)
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)
