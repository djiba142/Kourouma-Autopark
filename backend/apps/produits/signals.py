import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Produit

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Produit)
def alerte_stock_critique(sender, instance, **kwargs):
    """
    Déclenche une notification email quand le stock passe sous le seuil d'alerte.
    """
    if instance.actif and instance.quantite <= instance.seuil_alerte:
        subject = f"[ALERTE STOCK] {instance.nom} (Réf: {instance.reference})"
        message = (
            f"Le produit {instance.nom} a atteint un niveau de stock critique.\n\n"
            f"Stock actuel : {instance.quantite}\n"
            f"Seuil d'alerte : {instance.seuil_alerte}\n"
            f"Référence : {instance.reference}\n\n"
            f"Veuillez prévoir un réapprovisionnement rapidement.\n\n"
            f"BSG Dashboard"
        )
        
        try:
            # On envoie aux admins
            from auth_users.models import Utilisateur
            admins = Utilisateur.objects.filter(role='ADMIN', actif=True).values_list('email', flat=True)
            
            if admins:
                send_mail(
                    subject,
                    message,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bsg.com'),
                    list(admins),
                    fail_silently=True,
                )
                logger.info(f"Notification stock envoyée pour {instance.nom} à {list(admins)}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification stock : {e}")
