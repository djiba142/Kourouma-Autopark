from django.db import models
from django.db.models import Sum

class Client(models.Model):
    STATUTS = (
        ('BON', 'Bon Payeur'),
        ('MOYEN', 'Moyen'),
        ('MAUVAIS', 'Mauvais Payeur'),
        ('BLOQUE', 'Bloqué Manuellement'),
    )

    nom = models.CharField(max_length=150, verbose_name="Nom complet")
    telephone = models.CharField(max_length=20, unique=True, verbose_name="Téléphone")
    email = models.EmailField(null=True, blank=True, verbose_name="Adresse email")
    adresse = models.TextField(null=True, blank=True, verbose_name="Adresse de livraison")
    
    limite_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Limite de Crédit")
    score_statut = models.CharField(max_length=10, choices=STATUTS, default='BON')
    
    date_creation = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)

    @property
    def total_achats(self):
        return self.commandes.filter(statut='LIVREE').aggregate(total=Sum('total_ttc'))['total'] or 0

    @property
    def total_paye(self):
        from commandes.models import Paiement
        return Paiement.objects.filter(commande__client=self).aggregate(total=Sum('montant'))['total'] or 0

    @property
    def total_dette(self):
        # Dette = Somme de (total_ttc - deja_paye) pour toutes les commandes non annulées
        return self.total_achats - self.total_paye

    @property
    def alerte_credit(self):
        return self.total_dette > self.limite_credit

    def __str__(self):
        return f"{self.nom} ({self.telephone})"

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['nom']
