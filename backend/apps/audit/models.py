from django.db import models
from django.conf import settings
from django.utils import timezone

class AuditLog(models.Model):
    """
    Modèle unifié pour le Journal d'Audit (Web) et les Logs d'Activité (Mobile).
    Supporte les deux conventions de nommage pour ne pas casser l'API existante.
    """
    TYPES_ACTION = (
        ('CONNEXION', 'Connexion'),
        ('VENTE', 'Vente effectuée'),
        ('STOCK_ENTREE', 'Réapprovisionnement'),
        ('STOCK_SORTIE', 'Sortie de stock'),
        ('ACCES', 'Attribution accès'),
        ('SUPPRESSION', 'Suppression'),
        ('AUTRE', 'Autre action'),
    )

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audit_logs")
    
    # Champs Web (Dashboard)
    action      = models.CharField(max_length=255, verbose_name="Action (Web)")
    details     = models.TextField(null=True, blank=True, verbose_name="Détails (Web)")
    ip          = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP (Web)")
    date        = models.DateTimeField(auto_now_add=True, verbose_name="Date (Web)")

    # Champs Mobile API (Compatibilité - Null=True pour faciliter la migration)
    type_action = models.CharField(max_length=20, choices=TYPES_ACTION, default='AUTRE', verbose_name="Type (Mobile)")
    description = models.TextField(null=True, blank=True, verbose_name="Description (Mobile)")
    ip_adresse  = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP (Mobile)")
    date_evenement = models.DateTimeField(default=timezone.now, verbose_name="Date (Mobile)")

    def save(self, *args, **kwargs):
        # Synchronisation des champs pour que les données soient lisibles des deux côtés
        if not self.action and self.type_action:
            self.action = self.type_action
        if not self.details and self.description:
            self.details = self.description
        if not self.ip and self.ip_adresse:
            self.ip = self.ip_adresse
        
        # Et vice-versa
        if not self.type_action and self.action:
            # Essayer de mapper l'action textuelle vers un type mobile si possible
            action_upper = self.action.upper()
            if 'CONNEXION' in action_upper: self.type_action = 'CONNEXION'
            elif 'VENTE' in action_upper:   self.type_action = 'VENTE'
            elif 'STOCK' in action_upper:   self.type_action = 'STOCK_ENTREE'
            else: self.type_action = 'AUTRE'

        if not self.description and self.details:
            self.description = self.details
        if not self.ip_adresse and self.ip:
            self.ip_adresse = self.ip
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.utilisateur.email} - {self.action} - {self.date}"

    class Meta:
        verbose_name = "Log d'audit / Activité"
        verbose_name_plural = "Logs d'audit / Activité"
        ordering = ['-date']

# Alias pour le code mobile existant
LogActivite = AuditLog
