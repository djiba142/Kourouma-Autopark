from rest_framework import serializers
from django.db.models import Sum, Q
from .models import Localisation, StockParLocalisation, MouvementStock, TransfertStock, TransfertItem
from produits.serializers import ProduitSerializer


class LocalisationSerializer(serializers.ModelSerializer):
    total_valeur_stock = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    produits_alerte_count = serializers.SerializerMethodField()
    produits_rupture_count = serializers.SerializerMethodField()
    
    def get_produits_alerte_count(self, obj):
        return obj.inventaire.filter(
            quantite__lte=models.F('produit__seuil_alerte')
        ).count()
    
    def get_produits_rupture_count(self, obj):
        return obj.inventaire.filter(quantite=0).count()

    class Meta:
        model = Localisation
        fields = ['id', 'nom', 'type', 'type_display', 'adresse', 'actif', 
                 'total_valeur_stock', 'produits_alerte_count', 'produits_rupture_count']


class StockParLocalisationSerializer(serializers.ModelSerializer):
    produit_detail = ProduitSerializer(source='produit', read_only=True)
    localisation_nom = serializers.CharField(source='localisation.nom', read_only=True)
    valeur_stock = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    est_en_alerte = serializers.BooleanField(read_only=True)
    est_en_rupture = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = StockParLocalisation
        fields = ['id', 'produit', 'produit_detail', 'localisation', 'localisation_nom', 
                 'quantite', 'valeur_stock', 'est_en_alerte', 'est_en_rupture', 'date_maj']


class MouvementStockSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.username', read_only=True)
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_reference = serializers.CharField(source='produit.reference', read_only=True)
    localisation_nom = serializers.CharField(source='localisation.nom', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)

    class Meta:
        model = MouvementStock
        fields = ['id', 'produit', 'produit_nom', 'produit_reference', 'localisation', 'localisation_nom',
                 'type', 'type_display', 'quantite', 'unite', 'quantite_avant', 'quantite_apres',
                 'reference_doc', 'utilisateur_nom', 'date', 'notes']
        read_only_fields = ['quantite_avant', 'quantite_apres', 'utilisateur_nom', 'date']


class TransfertItemSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_reference = serializers.CharField(source='produit.reference', read_only=True)
    
    class Meta:
        model = TransfertItem
        fields = ['id', 'produit', 'produit_nom', 'produit_reference', 
                 'quantite_demandee', 'quantite_reelle']


class TransfertStockSerializer(serializers.ModelSerializer):
    items = TransfertItemSerializer(many=True, read_only=True)
    provenance_nom = serializers.CharField(source='provenance.nom', read_only=True)
    destination_nom = serializers.CharField(source='destination.nom', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.username', read_only=True)
    valide_par_nom = serializers.CharField(source='valide_par.username', read_only=True, allow_null=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)

    class Meta:
        model = TransfertStock
        fields = ['id', 'reference', 'provenance', 'provenance_nom', 'destination', 'destination_nom',
                 'statut', 'statut_display', 'items', 'cree_par_nom', 'valide_par_nom',
                 'date_creation', 'date_validation', 'date_reception']
        read_only_fields = ['reference', 'cree_par_nom', 'date_creation']
