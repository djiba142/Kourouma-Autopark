from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import JournalFinancier, EcritureComptable, CompteComptable, Depense
from commandes.models import Paiement, Commande

@receiver(post_save, sender=Paiement)
def journaliser_paiement(sender, instance, created, **kwargs):
    if not created: return
    try:
        with transaction.atomic():
            caisse, _ = CompteComptable.objects.get_or_create(code='101', defaults={'nom': 'Caisse Centale', 'type': 'ACTIF'})
            clients, _ = CompteComptable.objects.get_or_create(code='401', defaults={'nom': 'Clients / Créances', 'type': 'ACTIF'})
            journal = JournalFinancier.objects.create(
                type_operation='PAIEMENT', reference_doc=instance.numero,
                description=f"Encaissement paiement client pour commande {instance.commande.numero}",
                montant=instance.montant, montant_gnf=instance.montant,
                type_flux='ENTREE', utilisateur=instance.enregistre_par or instance.commande.cree_par
            )
            EcritureComptable.objects.create(journal=journal, compte=caisse, debit=instance.montant, credit=0)
            EcritureComptable.objects.create(journal=journal, compte=clients, debit=0, credit=instance.montant)
    except Exception as e:
        print(f"Erreur journalisation paiement: {e}")

@receiver(post_save, sender=Depense)
def journaliser_depense(sender, instance, created, **kwargs):
    if not created: return
    try:
        with transaction.atomic():
            charges, _ = CompteComptable.objects.get_or_create(code='602', defaults={'nom': 'Charges et Dépenses Diverses', 'type': 'CHARGE'})
            caisse, _ = CompteComptable.objects.get_or_create(code='101', defaults={'nom': 'Caisse Centale', 'type': 'ACTIF'})
            journal = JournalFinancier.objects.create(
                type_operation='DEPENSE', reference_doc=instance.numero,
                description=f"Dépense : {instance.description}",
                montant=instance.montant, devise=instance.devise, taux=instance.taux, montant_gnf=instance.montant_gnf,
                type_flux='SORTIE', utilisateur=instance.cree_par
            )
            EcritureComptable.objects.create(journal=journal, compte=charges, debit=instance.montant_gnf, credit=0)
            EcritureComptable.objects.create(journal=journal, compte=caisse, debit=0, credit=instance.montant_gnf)
    except Exception as e:
        print(f"Erreur journalisation dépense: {e}")

@receiver(post_save, sender=Commande)
def journaliser_vente(sender, instance, created, **kwargs):
    if instance.statut not in ['VALIDEE', 'LIVREE']: return
    if JournalFinancier.objects.filter(type_operation='VENTE', reference_doc=instance.numero).exists(): return
    try:
        with transaction.atomic():
            clients, _ = CompteComptable.objects.get_or_create(code='401', defaults={'nom': 'Clients / Créances', 'type': 'ACTIF'})
            ventes, _ = CompteComptable.objects.get_or_create(code='701', defaults={'nom': 'Ventes de Marchandises', 'type': 'PRODUIT'})
            journal = JournalFinancier.objects.create(
                type_operation='VENTE', reference_doc=instance.numero,
                description=f"Revenu de vente : {instance.numero}",
                montant=instance.total_ttc, montant_gnf=instance.total_ttc,
                type_flux='ENTREE', utilisateur=instance.cree_par
            )
            EcritureComptable.objects.create(journal=journal, compte=clients, debit=instance.total_ttc, credit=0)
            EcritureComptable.objects.create(journal=journal, compte=ventes, debit=0, credit=instance.total_ttc)
    except Exception as e:
        print(f"Erreur journalisation vente: {e}")
