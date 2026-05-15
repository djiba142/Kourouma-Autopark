import os
import django
import random
import string
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.text import slugify

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from auth_users.models import Utilisateur
from produits.models import Produit, Categorie
from clients.models import Client
from achats.models import Fournisseur, CommandeAchat, LigneAchat
from commandes.models import Commande, LigneCommande
from finances.models import JournalFinancier, CategorieDepense

def seed_data():
    print("--- Debut du peuplement des donnees IA ---")

    # 1. Création Admin (si n'existe pas)
    admin, created = Utilisateur.objects.get_or_create(
        email="admin@bsg.com",
        defaults={
            'nom': "Admin IA",
            'role': "ADMIN",
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password("admin123")
        admin.save()
        print("  - Admin cree (admin@bsg.com / admin123)")

    # 2. Localisation
    from stock.models import Localisation, StockParLocalisation
    loc, _ = Localisation.objects.get_or_create(
        nom="Magasin Principal",
        defaults={'type': 'MAGASIN', 'adresse': 'Conakry'}
    )

    # 3. Catégories et Produits
    def get_cat(name):
        c, _ = Categorie.objects.get_or_create(nom=name, defaults={'slug': slugify(name)})
        return c

    cat_frein = get_cat("Freinage")
    cat_moteur = get_cat("Moteur")
    cat_accessoire = get_cat("Accessoires")

    produits_data = [
        ("Plaquettes de frein Toyota", cat_frein, 250000, 350000, "PLQ-TYT-01", 50, 10),
        ("Disque de frein Mercedes", cat_frein, 800000, 1200000, "DSC-MB-02", 20, 2),
        ("Filtre a huile Hilux", cat_moteur, 45000, 75000, "FLT-HIL-03", 100, 50),
        ("Kit Courroie Distribution", cat_moteur, 1200000, 1800000, "KIT-COR-04", 10, 1),
        ("Alternateur 12V Universal", cat_moteur, 1500000, 2200000, "ALT-UNI-05", 5, 1),
        ("Huile Moteur 5W30 (5L)", cat_moteur, 350000, 500000, "HUL-5W30", 80, 24),
        ("Balais d'essuie-glace", cat_accessoire, 30000, 60000, "BLI-ESS-07", 200, 10),
        ("Batterie 75Ah Turbo", cat_accessoire, 650000, 950000, "BAT-75AH", 15, 1),
        ("Bougies d'allumage (x4)", cat_moteur, 100000, 180000, "BGJ-ALL-09", 40, 10),
        ("Turbo diesel RAV4", cat_moteur, 4500000, 6500000, "TRB-RAV4", 3, 1),
    ]

    produits = []
    for nom, cat, p_achat, p_vente, ref, stock, conv in produits_data:
        p, _ = Produit.objects.get_or_create(
            reference=ref,
            defaults={
                'nom': nom,
                'categorie': cat,
                'prix_achat': p_achat,
                'prix_vente': p_vente,
                'quantite': stock,
                'conversion_unit': conv,
                'code_barre': ''.join(random.choices(string.digits, k=13)),
                'seuil_alerte': 30 if "Plaquettes" in nom else 5,
                'actif': True
            }
        )
        StockParLocalisation.objects.update_or_create(
            produit=p, localisation=loc,
            defaults={'quantite': stock}
        )
        produits.append(p)
    print(f"  - {len(produits)} produits crees")

    # 4. Clients
    client1, _ = Client.objects.get_or_create(nom="Mamadou Diallo", defaults={'telephone':"622112233"})
    client2, _ = Client.objects.get_or_create(nom=" Garage Sylla", defaults={'telephone':"620445566"})
    clients = [client1, client2]
    print("  - Clients crees")

    # 5. Historique de Ventes (pour PredicteurVentes)
    maintenant = timezone.now()
    print("  - Simulation des ventes (60 jours)...")
    for p in produits:
        # Tendance forte pour le premier (pour déclencher alerte stock si stock=50 et vente_prevue J+7 > 50)
        vitesse_moyenne = 8 if p == produits[0] else random.randint(1, 3)
        tendance = 0.15 if p == produits[0] else 0

        for i in range(60):
            date_v = maintenant - timedelta(days=60-i)
            vol = max(0, int(vitesse_moyenne + (i * tendance) + random.randint(-1, 1)))
            if vol > 0:
                cmd = Commande.objects.create(
                    numero=f"CMD-{p.id}-{i}-{random.randint(1000,9999)}",
                    client=random.choice(clients),
                    cree_par=admin,
                    statut='LIVREE',
                    total_ttc=vol * p.prix_vente,
                    localisation=loc
                )
                # Forcer la date
                Commande.objects.filter(id=cmd.id).update(date_creation=date_v)
                LigneCommande.objects.create(
                    commande=cmd,
                    produit=p,
                    quantite=vol,
                    prix_unitaire=p.prix_vente,
                    sous_total=vol * p.prix_vente
                )

    # 6. Journal Financier (pour DetecteurAnomalies)
    print("  - Simulation du journal financier (30 jours)...")
    for i in range(40):
        date_op = maintenant - timedelta(days=random.randint(0, 30))
        date_op = date_op.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
        
        JournalFinancier.objects.create(
            utilisateur=admin,
            type_operation='DEPENSE',
            type_flux='SORTIE',
            montant=random.randint(50000, 500000),
            montant_gnf=0, # Sera calculé? Non, le modèle save() le gère? Ah non.
            description=f"Depense courante {i}",
            reference_doc=f"REF-{i}",
            date=date_op
        )

    # Anomalies
    JournalFinancier.objects.create(
        utilisateur=admin,
        type_operation='DEPENSE',
        type_flux='SORTIE',
        montant=25000000,
        montant_gnf=25000000,
        description="Achat suspect gros montant",
        reference_doc="ANOM-01",
        date=maintenant - timedelta(days=1)
    )
    nuit = (maintenant - timedelta(days=4)).replace(hour=2, minute=45)
    JournalFinancier.objects.create(
        utilisateur=admin,
        type_operation='DEPENSE',
        type_flux='SORTIE',
        montant=150000,
        montant_gnf=150000,
        description="Operation nocturne",
        reference_doc="ANOM-02",
        date=nuit
    )
    
    print("\nTermine ! Donnes IA pretes dans MySQL.")

if __name__ == "__main__":
    seed_data()
