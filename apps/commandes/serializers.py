from rest_framework import serializers
from .models import Commande, LigneCommande, Paiement
from produits.models import Produit
from produits.serializers import ProduitSerializer
from clients.serializers import ClientSerializer

class PaiementSerializer(serializers.ModelSerializer):
    mode_paiement_display = serializers.CharField(source='get_mode_paiement_display', read_only=True)
    
    class Meta:
        model = Paiement
        fields = ['id', 'montant', 'date_paiement', 'mode_paiement', 'mode_paiement_display', 'reference_transaction', 'numero']
        read_only_fields = ['numero', 'date_paiement']


class LigneCommandeSerializer(serializers.ModelSerializer):
    produit_details = ProduitSerializer(source='produit', read_only=True)
    total = serializers.SerializerMethodField()

    def get_total(self, obj):
        return float(obj.quantite) * float(obj.prix_unitaire)

    class Meta:
        model = LigneCommande
        fields = ['id', 'produit', 'produit_details', 'quantite', 'prix_unitaire', 'sous_total', 'total']
        read_only_fields = ['sous_total']


class CommandeSerializer(serializers.ModelSerializer):
    lignes = LigneCommandeSerializer(many=True, required=False)
    paiements = PaiementSerializer(many=True, read_only=True)
    reste_a_payer = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    client_details = serializers.StringRelatedField(source='client', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    statut_paiement_display = serializers.CharField(source='get_statut_paiement_display', read_only=True)
    type_vente_display = serializers.CharField(source='get_type_vente_display', read_only=True)
    type_remise_display = serializers.CharField(source='get_type_remise_display', read_only=True)

    class Meta:
        model = Commande
        fields = [
            'id', 'numero', 'client', 'client_details', 'statut', 'statut_display', 
            'statut_paiement', 'statut_paiement_display', 'type_vente', 'type_vente_display',
            'total_ht', 'type_remise', 'type_remise_display', 'remise', 'total_ttc', 
            'reste_a_payer', 'lignes', 'paiements', 'localisation', 'photo_colis', 
            'date_creation', 'date_validation', 'date_expedition', 'notes',
            'cree_par', 'prepare_par'
        ]
        read_only_fields = ['id', 'total_ht', 'total_ttc', 'date_creation', 'numero', 'reste_a_payer']

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes', [])
        commande = Commande.objects.create(**validated_data)
        for ligne_data in lignes_data:
            LigneCommande.objects.create(commande=commande, **ligne_data)
        return commande


class PanierSerializer(serializers.Serializer):
    """Sérialiseur pour le panier dynamique (lecture/écriture)"""
    commande_id = serializers.IntegerField()
    produit_id = serializers.IntegerField()
    quantite = serializers.IntegerField(min_value=1)
    prix_unitaire = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
