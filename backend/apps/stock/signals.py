from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import MouvementStock, StockParLocalisation, Produit
from django.db.models import Sum

@receiver(post_save, sender=MouvementStock)
def synchro_stock_localisation(sender, instance, created, **kwargs):
    if created:
        # 1. Update the localized stock
        stock_loc, _ = StockParLocalisation.objects.get_or_create(
            produit=instance.produit,
            localisation=instance.localisation
        )
        
        instance.quantite_avant = stock_loc.quantite
        
        # Determine the modifier
        if instance.type in ['ENTREE', 'AJUSTEMENT']:
            stock_loc.quantite += instance.quantite
        elif instance.type == 'SORTIE':
            stock_loc.quantite -= instance.quantite
            
        stock_loc.save()
        
        # 2. Update Audit Snapshots
        instance.quantite_apres = stock_loc.quantite
        instance.save(update_fields=['quantite_avant', 'quantite_apres'])
        
        # 3. Synchronize global Produit quantity (Ground Truth = Sum of Locals)
        total_global = StockParLocalisation.objects.filter(
            produit=instance.produit
        ).aggregate(total=Sum('quantite'))['total'] or 0
        
        instance.produit.quantite = total_global
        instance.produit.save(update_fields=['quantite'])
