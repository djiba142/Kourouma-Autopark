from rest_framework import serializers
from .models import Commande, LigneCommande, Paiement
from produits.models import Produit
from produits.serializers import ProduitSerializer
from clients.serializers import ClientSerializer # need to define this too

class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = ['id', 'montant', 'date_paiement', 'mode_paiement', 'reference_transaction']

class LigneCommandeSerializer(serializers.ModelSerializer):
    produit_details = ProduitSerializer(source='produit', read_only=True)

    class Meta:
        model = LigneCommande
        fields = ['id', 'produit', 'produit_details', 'quantite', 'prix_unitaire', 'sous_total']
        read_only_fields = ['sous_total']

class CommandeSerializer(serializers.ModelSerializer):
    lignes = LigneCommandeSerializer(many=True, required=False)
    paiements = PaiementSerializer(many=True, read_only=True)
    reste_a_payer = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    client_details = serializers.StringRelatedField(source='client', read_only=True)

    class Meta:
        model = Commande
        fields = [
            'id', 'numero', 'client', 'client_details', 'statut', 'statut_paiement', 
            'type_vente', 'total_ht', 'type_remise', 'remise', 'total_ttc', 
            'reste_a_payer', 'lignes', 'paiements', 'localisation', 'photo_colis', 
            'date_creation', 'notes'
        ]
        read_only_fields = ['id', 'total_ht', 'total_ttc', 'date_creation', 'numero']

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes', [])
        commande = Commande.objects.create(**validated_data)
        for ligne_data in lignes_data:
            LigneCommande.objects.create(commande=commande, **ligne_data)
        return commande
