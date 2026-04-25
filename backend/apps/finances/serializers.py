from rest_framework import serializers
from .models import CategorieDepense, Depense, CompteComptable, JournalFinancier, EcritureComptable

class CategorieDepenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategorieDepense
        fields = '__all__'

class DepenseSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    cree_par_nom = serializers.CharField(source='cree_par.nom', read_only=True)
    categorie = serializers.PrimaryKeyRelatedField(queryset=CategorieDepense.objects.all(), required=True)

    class Meta:
        model = Depense
        fields = [
            'id', 'numero', 'montant', 'devise', 'taux', 'montant_gnf', 'description', 
            'categorie', 'categorie_nom', 'date_depense', 'type_depense', 
            'periodicite', 'preuve', 'cree_par', 'cree_par_nom'
        ]
        read_only_fields = ['id', 'numero', 'montant_gnf', 'date_depense', 'cree_par']

class CompteComptableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteComptable
        fields = '__all__'

class EcritureComptableSerializer(serializers.ModelSerializer):
    compte_nom = serializers.CharField(source='compte.nom', read_only=True)
    compte_code = serializers.CharField(source='compte.code', read_only=True)

    class Meta:
        model = EcritureComptable
        fields = ['id', 'compte', 'compte_code', 'compte_nom', 'debit', 'credit']

class JournalFinancierSerializer(serializers.ModelSerializer):
    ecritures = EcritureComptableSerializer(many=True, read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.nom', read_only=True)

    class Meta:
        model = JournalFinancier
        fields = [
            'id', 'numero', 'date', 'type_operation', 'reference_doc', 
            'description', 'montant', 'devise', 'taux', 'montant_gnf', 
            'type_flux', 'utilisateur', 'utilisateur_nom', 'ecritures'
        ]
        read_only_fields = ['id', 'numero', 'created_at']
