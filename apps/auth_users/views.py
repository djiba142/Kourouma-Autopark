from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from datetime import timedelta
from .serializers import CustomTokenObtainPairSerializer, UtilisateurSerializer
from .models import Utilisateur
from .permissions import IsBSGAdmin
from audit.models import LogActivite

class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        try:
            user = Utilisateur.objects.get(email=email)
            
            # Check lockout (15 minutes)
            if user.tentatives_echouees >= 5:
                if user.derniere_tentative and timezone.now() < user.derniere_tentative + timedelta(minutes=15):
                    LogActivite.objects.create(
                        utilisateur=user,
                        type_action="ACCES",
                        description=f"Tentative de connexion sur compte bloqué (IP: {request.META.get('REMOTE_ADDR')})",
                        ip_adresse=request.META.get('REMOTE_ADDR')
                    )
                    return Response(
                        {"error": "Compte bloqué pour 15 minutes suite à trop d'échecs."},
                        status=status.HTTP_403_FORBIDDEN
                    )
                else:
                    # Reset after 15 mins
                    user.tentatives_echouees = 0
                    user.save()

        except Utilisateur.DoesNotExist:
            user = None

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            if user:
                user.tentatives_echouees = 0
                user.save()
                LogActivite.objects.create(
                    utilisateur=user,
                    type_action="CONNEXION",
                    description=f"Connexion réussie (IP: {request.META.get('REMOTE_ADDR')})",
                    ip_adresse=request.META.get('REMOTE_ADDR')
                )
        else:
            if user:
                user.tentatives_echouees += 1
                user.derniere_tentative = timezone.now()
                user.save()
                LogActivite.objects.create(
                    utilisateur=user,
                    type_action="CONNEXION",
                    description=f"Échec de connexion n°{user.tentatives_echouees} (IP: {request.META.get('REMOTE_ADDR')})",
                    ip_adresse=request.META.get('REMOTE_ADDR')
                )
        
        return response

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            LogActivite.objects.create(
                utilisateur=request.user,
                type_action="CONNEXION",
                description=f"Déconnexion réussie",
                ip_adresse=request.META.get('REMOTE_ADDR')
            )
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UtilisateurSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_update(self, serializer):
        user = serializer.save()
        LogActivite.objects.create(
            utilisateur=user,
            type_action="ACCES",
            description="Mise à jour des informations de profil",
            ip_adresse=self.request.META.get('REMOTE_ADDR')
        )

class RegisterEmployeView(generics.CreateAPIView):
    serializer_class = UtilisateurSerializer
    permission_classes = [IsBSGAdmin]

    def perform_create(self, serializer):
        password = self.request.data.get('password', 'BSG_Pass2026!')
        user = serializer.save(role='EMPLOYE')
        user.set_password(password)
        user.save()
        
        LogActivite.objects.create(
            utilisateur=self.request.user,
            type_action="ACCES",
            description=f"Création de l'employé: {user.nom} ({user.email})",
            ip_adresse=self.request.META.get('REMOTE_ADDR')
        )
