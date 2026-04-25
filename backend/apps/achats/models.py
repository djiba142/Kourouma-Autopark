from django.db import models
from django.conf import settings
from produits.models import Produit
from stock.models import Localisation

class Fournisseur(models.Model):
    DEVISES = (
        ('GNF', 'Franc Guinéen'),
        ('USD', 'Dollar US'),
        ('EUR', 'Euro'),
    )
    
    TYPES = (
        ('LOCAL', 'Fournisseur Local'),
        ('INTERNATIONAL', 'Importateur / International'),
    )

    nom = models.CharField(max_length=200, unique=True)
    pays = models.CharField(max_length=100, default='Guinée')
    type = models.CharField(max_length=20, choices=TYPES, default='LOCAL')
    devise_par_defaut = models.CharField(max_length=3, choices=DEVISES, default='GNF')
    
    telephone = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    adresse = models.TextField(null=True, blank=True)
    
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nom} ({self.pays})"

    class Meta:
        verbose_name = "Fournisseur"
        verbose_name_plural = "Fournisseurs"

class CommandeAchat(models.Model):
    STATUTS = (
        ('BROUILLON', 'Brouillon'),
        ('ENVOYEE', 'Envoyée au fournisseur'),
        ('RECUE', 'Marchandise Reçue (En Stock)'),
        ('ANNULEE', 'Annulée'),
    )

    reference = models.CharField(max_length=50, unique=True, verbose_name="N° Bon de Commande")
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, related_name="achats")
    statut = models.CharField(max_length=20, choices=STATUTS, default='BROUILLON')
    
    devise = models.CharField(max_length=3, choices=Fournisseur.DEVISES, default='USD')
    taux_change = models.DecimalField(max_digits=12, decimal_places=4, default=1, help_text="Taux pour conversion en GNF")
    
    total_devise = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_gnf = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="achats_crees")
    date_commande = models.DateField(verbose_name="Date de commande")
    date_reception_prevue = models.DateField(null=True, blank=True)
    date_reception_reelle = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"PO {self.reference} - {self.fournisseur.nom}"

    class Meta:
        verbose_name = "Commande d'Achat"
        verbose_name_plural = "Commandes d'Achat"
        ordering = ['-date_commande']

class LigneAchat(models.Model):
    achat = models.ForeignKey(CommandeAchat, on_delete=models.CASCADE, related_name="lignes")
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    
    quantite_cartons = models.IntegerField(verbose_name="Quantité (Cartons)")
    quantite_pieces = models.IntegerField(verbose_name="Equiv. Pièces", editable=False)
    
    prix_unitaire_devise = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prix Unitaire (Devise)")
    sous_total_devise = models.DecimalField(max_digits=15, decimal_places=2, editable=False)
    sous_total_gnf = models.DecimalField(max_digits=15, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        # Auto-calculate quantities and totals
        self.quantite_pieces = self.quantite_cartons * self.produit.conversion_unit
        self.sous_total_devise = self.quantite_cartons * self.prix_unitaire_devise
        self.sous_total_gnf = self.sous_total_devise * self.achat.taux_change
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Ligne d'Achat"
        verbose_name_plural = "Lignes d'Achat"
