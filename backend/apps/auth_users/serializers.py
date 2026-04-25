from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import Utilisateur

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'nom': self.user.nom,
            'role': self.user.role,
        }
        return data

class UtilisateurSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Utilisateur
        fields = ['id', 'email', 'nom', 'role', 'actif', 'fcm_token', 'date_creation', 'password']
        read_only_fields = ['id', 'date_creation']

    def validate_password(self, value):
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins un chiffre.")
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError("Le mot de passe doit contenir au moins une lettre.")
        return value
