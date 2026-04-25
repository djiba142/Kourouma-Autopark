from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from produits.models import Produit
from clients.models import Client

class Commande(models.Model):
    STATUTS = (
        ('EN_ATTENTE', 'En attente'),
        ('VALIDEE', 'Validée'),
        ('EN_PREPARATION', 'En préparation'),
        ('PRETE', 'Prête'),
        ('EXPEDIEE', 'Expédiée'),
        ('LIVREE', 'Livrée'),
        ('ANNULEE', 'Annulée'),
    )

    PAIEMENT_STATUTS = (
        ('NON_PAYE', 'Non payé'),
        ('PARTIEL', 'Partiel'),
        ('PAYE', 'Payé'),
    )

    TYPES_VENTE = (
        ('COMMANDE', 'Commande à distance'),
        ('VENTE_DIRECTE', 'Vente directe au comptoir'),
    )

    REMISE_CHOICES = (
        ('FIXE', 'Montant fixe (GNF)'),
        ('POURCENT', 'Pourcentage (%)'),
    )

    numero = models.CharField(max_length=50, unique=True, verbose_name="N° Commande")
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name="commandes")
    statut = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    statut_paiement = models.CharField(max_length=20, choices=PAIEMENT_STATUTS, default='NON_PAYE')
    type_vente = models.CharField(max_length=20, choices=TYPES_VENTE, default='COMMANDE')
    
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    type_remise = models.CharField(max_length=10, choices=REMISE_CHOICES, default='POURCENT')
    remise = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Valeur Remise")
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    localisation = models.ForeignKey('stock.Localisation', on_delete=models.SET_NULL, null=True, blank=True, related_name="commandes_site")
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="commandes_creees")
    prepare_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="commandes_preparees")
    photo_colis = models.ImageField(upload_to='colis/', null=True, blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_expedition = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    @property
    def reste_a_payer(self):
        total_paye = sum(p.montant for p in self.paiements.all())
        return self.total_ttc - total_paye

    def __str__(self):
        return self.numero

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_creation']

class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.IntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2)
    sous_total = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.sous_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

class Paiement(models.Model):
    MODES = (
        ('CASH', 'Espèces'),
        ('MOBILE_MONEY', 'Mobile Money'),
        ('VIREMENT', 'Virement Bancaire'),
        ('DIVERS', 'Autre'),
    )

    numero = models.CharField(max_length=50, unique=True, editable=False, null=True, verbose_name="N° Paiement")
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="paiements")
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_paiement = models.DateTimeField(auto_now_add=True)
    mode_paiement = models.CharField(max_length=20, choices=MODES, default='CASH')
    reference_transaction = models.CharField(max_length=100, null=True, blank=True, verbose_name="Réf. Transaction (Mobile Money)")
    preuve_paiement = models.ImageField(upload_to='paiements/preuves/', null=True, blank=True)
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(_("Un paiement ne peut pas être modifié après enregistrement."))
        
        if not self.numero:
            import datetime
            date_str = datetime.date.today().strftime('%Y%m')
            last_pay = Paiement.objects.filter(numero__contains=f"PAY-{date_str}").order_by('-numero').first()
            if last_pay:
                last_num = int(last_pay.numero.split('-')[-1])
                new_num = str(last_num + 1).zfill(4)
            else:
                new_num = "0001"
            self.numero = f"PAY-{date_str}-{new_num}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Paiement {self.montant} pour {self.commande.numero}"

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
