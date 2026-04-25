import os
import django

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.apps import apps
from django.db import transaction

def purge_data():
    print("🚀 Démarrage de la purge des données de démonstration...")
    
    # Liste des modèles à vider (ordre respectant les clés étrangères)
    models_to_clear = [
        ('commandes', 'LigneCommande'),
        ('commandes', 'Vente'),
        ('commandes', 'Commande'),
        ('achats', 'LigneAchat'),
        ('achats', 'Achat'),
        ('stock', 'MouvementStock'),
        ('stock', 'EntreeStock'),
        ('finances', 'EcritureComptable'),
        ('finances', 'JournalFinancier'),
        ('finances', 'Depense'),
        ('audit', 'AuditLog'),
        ('produits', 'HistoriquePrix'),
        ('produits', 'Produit'),
        ('produits', 'Marque'),
        ('produits', 'Categorie'),
        ('clients', 'Client'),
    ]

    try:
        with transaction.atomic():
            for app_label, model_name in models_to_clear:
                try:
                    model = apps.get_model(app_label, model_name)
                    count, _ = model.objects.all().delete()
                    print(f"✅ {app_label}.{model_name} : {count} entrées supprimées.")
                except LookupError:
                    print(f"⚠️ Modèle {app_label}.{model_name} non trouvé, passage...")

            print("\n🌟 Purge terminée avec succès !")
            print("☝️  Note : Les utilisateurs et le Plan Comptable ont été préservés.")
            
    except Exception as e:
        print(f"❌ Erreur lors de la purge : {e}")

if __name__ == "__main__":
    purge_data()
