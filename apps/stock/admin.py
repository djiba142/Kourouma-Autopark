from django.contrib import admin
from .models import Localisation, StockParLocalisation, MouvementStock, TransfertStock, TransfertItem

@admin.register(Localisation)
class LocalisationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type', 'actif')
    list_filter = ('type', 'actif')

@admin.register(StockParLocalisation)
class StockParLocalisationAdmin(admin.ModelAdmin):
    list_display = ('produit', 'localisation', 'quantite')
    list_filter = ('localisation',)
    search_fields = ('produit__nom', 'produit__reference')

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('date', 'produit', 'localisation', 'type', 'quantite', 'utilisateur')
    list_filter = ('type', 'localisation', 'date')
    search_fields = ('produit__nom', 'reference_doc')
    readonly_fields = ('date', 'quantite_avant', 'quantite_apres')

class TransfertItemInline(admin.TabularInline):
    model = TransfertItem
    extra = 0

@admin.register(TransfertStock)
class TransfertStockAdmin(admin.ModelAdmin):
    list_display = ('reference', 'provenance', 'destination', 'statut', 'date_creation')
    list_filter = ('statut', 'provenance', 'destination')
    search_fields = ('reference',)
    inlines = [TransfertItemInline]
