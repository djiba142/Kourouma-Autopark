from rest_framework import serializers
from .models import LogActivite

class LogActiviteSerializer(serializers.ModelSerializer):
    utilisateur_email = serializers.EmailField(source='utilisateur.email', read_only=True)

    class Meta:
        model = LogActivite
        fields = ['id', 'utilisateur_email', 'type_action', 'description', 'date_evenement', 'ip_adresse']
