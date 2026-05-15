from django.db import models, transaction
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import datetime

class CategorieDepense(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    budget_mensuel = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Budget mensuel (GNF)")
    
    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Catégorie de dépense"
        verbose_name_plural = "Catégories de dépenses"

class Depense(models.Model):
    TYPES = (
        ('ENTREPRISE', 'Professionnelle'),
        ('PERSONNEL', 'Personnelle'),
    )

    DEVISES = (
        ('GNF', 'Franc Guinéen'),
        ('USD', 'Dollar US'),
    )

    PERIODES = (
        ('JOUR', 'Journalier'),
        ('SEMAINE', 'Hebdomadaire'),
        ('MOIS', 'Mensuel'),
        ('AN', 'Annuel'),
    )

    numero = models.CharField(max_length=50, unique=True, editable=False, null=True, verbose_name="N° Dépense")
    montant = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Montant")
    devise = models.CharField(max_length=3, choices=DEVISES, default='GNF')
    taux = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    montant_gnf = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    
    description = models.TextField(verbose_name="Description")
    categorie = models.ForeignKey(CategorieDepense, on_delete=models.SET_NULL, null=True, related_name="depenses")
    date_depense = models.DateTimeField(auto_now_add=True, verbose_name="Date de dépense")
    type_depense = models.CharField(max_length=20, choices=TYPES, default='ENTREPRISE')
    periodicite = models.CharField(max_length=20, choices=PERIODES, default='JOUR')
    
    preuve = models.ImageField(upload_to='depenses/preuves/', null=True, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="depenses_enregistrees")

    def save(self, *args, **kwargs):
        # Prevent modification of existing entries
        if self.pk:
            raise ValidationError(_("Une dépense ne peut pas être modifiée après enregistrement."))
            
        # Automatic conversion
        if self.devise == 'GNF':
            self.montant_gnf = self.montant
            self.taux = 1.0
        else:
            self.montant_gnf = self.montant * self.taux
            
        # Generate sequence number if not exists
        if not self.numero:
            date_str = datetime.date.today().strftime('%Y%m')
            last_dep = Depense.objects.filter(numero__contains=f"DEP-{date_str}").order_by('-numero').first()
            if last_dep:
                last_num = int(last_dep.numero.split('-')[-1])
                new_num = str(last_num + 1).zfill(4)
            else:
                new_num = "0001"
            self.numero = f"DEP-{date_str}-{new_num}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.montant} ({self.type_depense}) - {self.description[:30]}"

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ['-date_depense']

# ──────────────────────────────────────────────────────────────────────────────
# 🏦 SYSTÈME COMPTABLE PRO
# ──────────────────────────────────────────────────────────────────────────────

class CompteComptable(models.Model):
    TYPES = (
        ('ACTIF', 'Actif (Caisse, Banque, Stock)'),
        ('PASSIF', 'Passif (Dettes, Capitaux)'),
        ('CHARGE', 'Charge (Dépenses, Achats)'),
        ('PRODUIT', 'Produit (Ventes, Revenus)'),
    )
    code = models.CharField(max_length=10, unique=True, verbose_name="Code Compte")
    nom = models.CharField(max_length=100, verbose_name="Nom du compte")
    type = models.CharField(max_length=10, choices=TYPES)

    def __str__(self):
        return f"{self.code} - {self.nom}"

    class Meta:
        verbose_name = "Compte Comptable"
        verbose_name_plural = "Comptes Comptables"
        ordering = ['code']

class JournalFinancier(models.Model):
    OPERATIONS = (
        ('VENTE', 'Vente Client'),
        ('PAIEMENT', 'Paiement Client'),
        ('DEPENSE', 'Dépense / Frais'),
        ('ACHAT', 'Achat Fournisseur'),
        ('AJUSTEMENT', 'Ajustement Manuel'),
    )
    FLUX = (
        ('ENTREE', 'Encaissement (+)'),
        ('SORTIE', 'Décaissement (-)'),
    )

    numero = models.CharField(max_length=50, unique=True, editable=False, verbose_name="N° Journal")
    date = models.DateTimeField(default=datetime.datetime.now)
    type_operation = models.CharField(max_length=20, choices=OPERATIONS)
    reference_doc = models.CharField(max_length=100, verbose_name="Réf Document")
    description = models.TextField()
    
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    devise = models.CharField(max_length=3, default='GNF')
    taux = models.DecimalField(max_digits=12, decimal_places=4, default=1.0)
    montant_gnf = models.DecimalField(max_digits=15, decimal_places=2)
    
    type_flux = models.CharField(max_length=10, choices=FLUX)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Une écriture au journal est IMMUTABLE et ne peut être modifiée.")
        
        if not self.numero:
            date_prefix = datetime.date.today().strftime('%Y%j') # Année + Jour de l'année
            with transaction.atomic():
                last_jrn = JournalFinancier.objects.filter(numero__contains=f"JRN-{date_prefix}").order_by('-numero').select_for_update().first()
                if last_jrn:
                    last_num = int(last_jrn.numero.split('-')[-1])
                    new_num = str(last_num + 1).zfill(4)
                else:
                    new_num = "0001"
                self.numero = f"JRN-{date_prefix}-{new_num}"
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.numero} | {self.type_operation} | {self.montant_gnf} GNF"

    class Meta:
        verbose_name = "Journal Financier"
        verbose_name_plural = "Journal Financier"
        ordering = ['-created_at']

class EcritureComptable(models.Model):
    journal = models.ForeignKey(JournalFinancier, on_delete=models.CASCADE, related_name="ecritures")
    compte = models.ForeignKey(CompteComptable, on_delete=models.PROTECT, related_name="ecritures")
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.journal.numero} | {self.compte.code} | D:{self.debit} C:{self.credit}"

    class Meta:
        verbose_name = "Écriture Comptable"
        verbose_name_plural = "Écritures Comptables"
