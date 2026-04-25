from django.db import models
from commandes.models import Commande

class Facture(models.Model):
    STATUTS = (
        ('EN_ATTENTE', 'En attente'),
        ('PARTIELLE', 'Paiement partiel'),
        ('PAIEE', 'Payée'),
        ('ANNULEE', 'Annulée'),
    )

    numero = models.CharField(max_length=50, unique=True, verbose_name="N° Facture")
    commande = models.OneToOneField(Commande, on_delete=models.CASCADE, related_name="facture")
    
    date_emission = models.DateTimeField(auto_now_add=True)
    date_echeance = models.DateField(null=True, blank=True)
    
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2)
    montant_regle = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reste_a_payer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    statut = models.CharField(max_length=20, choices=STATUTS, default='EN_ATTENTE')
    fichier_pdf = models.FileField(upload_to='factures/%Y/%m/', null=True, blank=True)

    def save(self, *args, **kwargs):
        self.reste_a_payer = self.total_ttc - self.montant_regle
        if self.montant_regle >= self.total_ttc:
            self.statut = 'PAIEE'
        elif self.montant_regle > 0:
            self.statut = 'PARTIELLE'
        else:
            self.statut = 'EN_ATTENTE'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.numero

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_emission']
