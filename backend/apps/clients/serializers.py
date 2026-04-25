from rest_framework import serializers
from .models import Client

class ClientSerializer(serializers.ModelSerializer):
    total_dette = serializers.ReadOnlyField()
    total_paye = serializers.ReadOnlyField()
    total_achats = serializers.ReadOnlyField()
    alerte_credit = serializers.ReadOnlyField()

    class Meta:
        model = Client
        fields = [
            'id', 'nom', 'telephone', 'email', 'adresse', 
            'limite_credit', 'score_statut', 'total_dette', 
            'total_paye', 'total_achats', 'alerte_credit',
            'date_creation', 'actif'
        ]
        read_only_fields = ['id', 'date_creation', 'total_dette', 'total_paye', 'total_achats', 'alerte_credit']
