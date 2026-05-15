from django.contrib import admin
from .models import Categorie, Marque, Produit, HistoriquePrix

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'slug')
    prepopulated_fields = {'slug': ('nom',)}

@admin.register(Marque)
class MarqueAdmin(admin.ModelAdmin):
    list_display = ('nom',)

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('reference', 'nom', 'categorie', 'marque_rel', 'prix_vente', 'quantite')
    list_filter = ('categorie', 'marque_rel', 'achat_devise')
    search_fields = ('reference', 'nom')
    readonly_fields = ('quantite', 'ajoute_par')

@admin.register(HistoriquePrix)
class HistoriquePrixAdmin(admin.ModelAdmin):
    list_display = ('produit', 'ancien_prix', 'nouveau_prix', 'date_modification', 'modifie_par')
    list_filter = ('date_modification',)
    readonly_fields = ('date_modification', 'modifie_par')
