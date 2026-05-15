from rest_framework import serializers
from .models import Produit, Categorie, Marque, HistoriquePrix

class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom', 'slug']

class MarqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Marque
        fields = ['id', 'nom', 'logo']

class HistoriquePrixSerializer(serializers.ModelSerializer):
    modifie_par_nom = serializers.CharField(source='modifie_par.get_full_name', read_only=True)

    class Meta:
        model = HistoriquePrix
        fields = ['id', 'ancien_prix', 'nouveau_prix', 'modifie_par_nom', 'date_modification']

class ProduitSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    marque_nom = serializers.CharField(source='marque_rel.nom', read_only=True)
    est_en_alerte = serializers.BooleanField(read_only=True)
    benefice = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    taux_marge = serializers.FloatField(read_only=True)

    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'reference', 'categorie', 'categorie_nom',
            'marque', 'marque_rel', 'marque_nom',
            'prix_achat', 'prix_achat_devise', 'achat_devise', 'taux_change_achat',
            'prix_vente', 'benefice', 'taux_marge',
            'unite_principale', 'unite_secondaire', 'conversion_unit',
            'quantite', 'seuil_alerte', 'est_en_alerte', 'image', 'actif',
            'date_ajout', 'historique_prix'
        ]
        read_only_fields = ['id', 'benefice', 'taux_marge']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Security: EMPLOYE cannot see purchase prices or margins
        if request and hasattr(request, 'user') and request.user.role == 'EMPLOYE':
            data.pop('prix_achat', None)
            data.pop('benefice', None)
            data.pop('taux_marge', None)
            
        return data
