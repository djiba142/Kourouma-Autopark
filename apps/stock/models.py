from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from produits.models import Produit


class Localisation(models.Model):
    TYPES = (
        ('MAGASIN', 'Magasin (Stock principal)'),
        ('BOUTIQUE', 'Boutique (Point de vente)'),
    )
    nom = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=10, choices=TYPES, default='MAGASIN')
    adresse = models.TextField(null=True, blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"
    
    @property
    def total_valeur_stock(self):
        """Valeur totale du stock à cette localisation"""
        return sum(
            float(item.quantite) * float(item.produit.prix_achat)
            for item in self.inventaire.all()
        )
    
    @property
    def produits_en_alerte(self):
        """Produits sous le seuil d'alerte"""
        return self.inventaire.filter(quantite__lte=models.F('produit__seuil_alerte'))
    
    @property
    def produits_en_rupture(self):
        """Produits en rupture (0 stock)"""
        return self.inventaire.filter(quantite=0)

    class Meta:
        verbose_name = "Localisation"
        verbose_name_plural = "Localisations"


class StockParLocalisation(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="stocks_locations")
    localisation = models.ForeignKey(Localisation, on_delete=models.CASCADE, related_name="inventaire")
    quantite = models.IntegerField(default=0, help_text="Quantité en unité secondaire (pièces)")
    date_maj = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.quantite < 0:
            raise ValidationError("Le stock ne peut pas être négatif.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def valeur_stock(self):
        """Valeur du stock pour ce produit à cette localisation"""
        return float(self.quantite) * float(self.produit.prix_achat)
    
    @property
    def est_en_alerte(self):
        """Produit sous seuil d'alerte?"""
        return self.quantite <= self.produit.seuil_alerte
    
    @property
    def est_en_rupture(self):
        """Produit en rupture?"""
        return self.quantite == 0

    def __str__(self):
        return f"{self.produit.nom} @ {self.localisation.nom}: {self.quantite}"

    class Meta:
        unique_together = ('produit', 'localisation')
        verbose_name = "Stock par Localisation"
        verbose_name_plural = "Stocks par Localisation"
        indexes = [
            models.Index(fields=['localisation', 'quantite']),
        ]


class MouvementStock(models.Model):
    TYPES = (
        ('ENTREE', 'Entrée de stock'),
        ('SORTIE', 'Sortie de stock'),
        ('TRANSFERT', 'Transfert inter-sites'),
        ('AJUSTEMENT', 'Ajustement manuel'),
    )

    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="mouvements")
    localisation = models.ForeignKey(Localisation, on_delete=models.CASCADE, related_name="mouvements", null=True)
    
    type = models.CharField(max_length=12, choices=TYPES)
    quantite = models.IntegerField(verbose_name="Quantité (base)")
    unite = models.CharField(max_length=20, default='PIECE')
    
    # Snapshots (Audit)
    quantite_avant = models.IntegerField(verbose_name="Stock avant", default=0)
    quantite_apres = models.IntegerField(verbose_name="Stock après", default=0)
    
    reference_doc = models.CharField(max_length=100, null=True, blank=True, verbose_name="Réf Doc")
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="mouvements_stock")
    date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"[{self.type}] {self.produit.nom} x {self.quantite}"

    class Meta:
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['produit', '-date']),
        ]


class TransfertStock(models.Model):
    STATUTS = (
        ('PROPOSE', 'En attente'),
        ('VALIDE', 'Validé pour préparation'),
        ('EXPEDIE', 'En transit'),
        ('RECU', 'Reçu en boutique'),
        ('ANNULE', 'Annulé'),
    )

    reference = models.CharField(max_length=50, unique=True)
    provenance = models.ForeignKey(Localisation, on_delete=models.CASCADE, related_name="transferts_sortants")
    destination = models.ForeignKey(Localisation, on_delete=models.CASCADE, related_name="transferts_entrants")
    
    statut = models.CharField(max_length=15, choices=STATUTS, default='PROPOSE')
    
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="transferts_crees")
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="transferts_valides")
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    date_reception = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Transfert {self.reference} ({self.statut})"
    
    class Meta:
        verbose_name = "Transfert de Stock"
        verbose_name_plural = "Transferts de Stock"
        ordering = ['-date_creation']


class TransfertItem(models.Model):
    """Items individuels d'un transfert"""
    transfert = models.ForeignKey(TransfertStock, on_delete=models.CASCADE, related_name="items")
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    quantite_demandee = models.IntegerField()
    quantite_reelle = models.IntegerField(default=0, help_text="Quantité réellement expédiée/reçue")
    
    def __str__(self):
        return f"{self.produit.nom} x {self.quantite_demandee}"
    
    class Meta:
        unique_together = ('transfert', 'produit')
        verbose_name = "Article Transfert"
        verbose_name_plural = "Articles Transfert"
