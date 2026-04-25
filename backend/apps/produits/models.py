from django.db import models
from django.conf import settings

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True, verbose_name="Nom de la catégorie")
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

class Marque(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to='marques/', null=True, blank=True)

    def __str__(self):
        return self.nom

class Produit(models.Model):
    nom = models.CharField(max_length=200, verbose_name="Nom commercial")
    reference = models.CharField(max_length=100, unique=True, verbose_name="Référence fabricant")
    categorie = models.ForeignKey(Categorie, on_delete=models.SET_NULL, null=True, related_name="produits")
    marque_rel = models.ForeignKey(Marque, on_delete=models.SET_NULL, null=True, blank=True, related_name="produits", verbose_name="Marque")
    marque = models.CharField(max_length=100, verbose_name="Marque (Texte)") # Keeping for compatibility for now
    
    # Financials (Multi-currency support)
    DEVISES = (
        ('GNF', 'Franc Guinéen'),
        ('USD', 'Dollar US'),
        ('EUR', 'Euro'),
    )
    achat_devise = models.CharField(max_length=3, choices=DEVISES, default='GNF', verbose_name="Devise d'achat")
    prix_achat_devise = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Prix d'achat (Devise)")
    taux_change_achat = models.DecimalField(max_digits=12, decimal_places=6, default=1, verbose_name="Taux de change (Achat)")
    
    prix_achat = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prix d'achat (Equiv. GNF)")
    prix_vente = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Prix de vente (GNF)")
    
    # Inventory Units (Carton vs Pièce)
    unite_principale = models.CharField(max_length=20, default='CARTON', verbose_name="Unité principale")
    unite_secondaire = models.CharField(max_length=20, default='PIECE', verbose_name="Unité secondaire")
    conversion_unit = models.IntegerField(default=20, help_text="Combien d'unités secondaires dans une unité principale (ex: 20 pièces dans 1 carton)")

    quantite = models.IntegerField(default=0, verbose_name="Quantité totale (Unité secondaire)")
    seuil_alerte = models.IntegerField(default=5, verbose_name="Seuil d'alerte")
    code_barre = models.CharField(max_length=50, unique=True, verbose_name="Code-barres")
    image = models.ImageField(upload_to='produits/', null=True, blank=True, verbose_name="Photo du produit")
    actif = models.BooleanField(default=True, verbose_name="Actif")
    date_ajout = models.DateTimeField(auto_now_add=True)
    ajoute_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="produits_ajoutes")

    @property
    def benefice(self):
        return self.prix_vente - self.prix_achat

    @property
    def taux_marge(self):
        if self.prix_achat > 0:
            return (self.benefice / self.prix_achat) * 100
        return 0

    @property
    def est_en_alerte(self):
        return self.quantite <= self.seuil_alerte

    def __str__(self):
        return f"{self.nom} ({self.reference})"

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['nom']

class HistoriquePrix(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="historique_prix")
    ancien_prix = models.DecimalField(max_digits=12, decimal_places=2)
    nouveau_prix = models.DecimalField(max_digits=12, decimal_places=2)
    modifie_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date_modification = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historique de Prix"
        verbose_name_plural = "Historiques de Prix"
        ordering = ['-date_modification']
