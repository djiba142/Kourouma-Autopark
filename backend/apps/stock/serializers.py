from rest_framework import serializers
from .models import Localisation, StockParLocalisation, MouvementStock, TransfertStock, TransfertItem
from produits.serializers import ProduitSerializer

class LocalisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localisation
        fields = '__all__'

class StockParLocalisationSerializer(serializers.ModelSerializer):
    produit_detail = ProduitSerializer(source='produit', read_only=True)
    localisation_nom = serializers.CharField(source='localisation.nom', read_only=True)
    
    class Meta:
        model = StockParLocalisation
        fields = ['id', 'produit', 'produit_detail', 'localisation', 'localisation_nom', 'quantite']

class MouvementStockSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    localisation_nom = serializers.CharField(source='localisation.nom', read_only=True)

    class Meta:
        model = MouvementStock
        fields = '__all__'
        read_only_fields = ['quantite_avant', 'quantite_apres', 'utilisateur', 'date']

class TransfertItemSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    
    class Meta:
        model = TransfertItem
        fields = ['id', 'produit', 'produit_nom', 'quantite_demandee', 'quantite_reelle']

class TransfertStockSerializer(serializers.ModelSerializer):
    items = TransfertItemSerializer(many=True, read_only=True)
    provenance_nom = serializers.CharField(source='provenance.nom', read_only=True)
    destination_nom = serializers.CharField(source='destination.nom', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.username', read_only=True)

    class Meta:
        model = TransfertStock
        fields = '__all__'
        read_only_fields = ['reference', 'cree_par', 'date_creation']
