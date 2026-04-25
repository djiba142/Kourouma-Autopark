from django.db import models
from django.conf import settings

class LogActivite(models.Model):
    TYPES_ACTION = (
        ('CONNEXION', 'Connexion'),
        ('VENTE', 'Vente effectuée'),
        ('STOCK_ENTREE', 'Réapprovisionnement'),
        ('STOCK_SORTIE', 'Sortie de stock'),
        ('ACCES', 'Attribution accès'),
        ('SUPPRESSION', 'Suppression'),
    )

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="logs")
    type_action = models.CharField(max_length=20, choices=TYPES_ACTION)
    description = models.TextField()
    date_evenement = models.DateTimeField(auto_now_add=True)
    ip_adresse = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.utilisateur.email} - {self.type_action} - {self.date_evenement}"

    class Meta:
        verbose_name = "Log d'activité"
        verbose_name_plural = "Logs d'activité"
        ordering = ['-date_evenement']
