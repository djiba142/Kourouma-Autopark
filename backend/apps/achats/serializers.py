from rest_framework import serializers
from .models import Fournisseur, CommandeAchat, LigneAchat
from produits.serializers import ProduitSerializer

class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = '__all__'

class LigneAchatSerializer(serializers.ModelSerializer):
    produit_details = ProduitSerializer(source='produit', read_only=True)

    class Meta:
        model = LigneAchat
        fields = ['id', 'produit', 'produit_details', 'quantite_cartons', 'quantite_pieces', 'prix_unitaire_devise', 'sous_total_devise', 'sous_total_gnf']
        read_only_fields = ['quantite_pieces', 'sous_total_devise', 'sous_total_gnf']

class CommandeAchatSerializer(serializers.ModelSerializer):
    lignes = LigneAchatSerializer(many=True, required=False)
    fournisseur_details = FournisseurSerializer(source='fournisseur', read_only=True)

    class Meta:
        model = CommandeAchat
        fields = [
            'id', 'reference', 'fournisseur', 'fournisseur_details', 'statut', 
            'devise', 'taux_change', 'total_devise', 'total_gnf', 
            'cree_par', 'date_commande', 'date_reception_prevue', 
            'date_reception_reelle', 'lignes', 'notes'
        ]
        read_only_fields = ['id', 'reference', 'total_devise', 'total_gnf', 'cree_par']

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes', [])
        achat = CommandeAchat.objects.create(**validated_data)
        for ligne_data in lignes_data:
            # We use the model instance to ensure save() is called for calculations
            ligne = LigneAchat(achat=achat, **ligne_data)
            ligne.save()
        return achat
