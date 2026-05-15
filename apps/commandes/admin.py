from django.contrib import admin
from .models import Commande, LigneCommande, Paiement

class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 0

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('numero', 'client', 'statut', 'total_ttc', 'date_creation')
    list_filter = ('statut', 'date_creation')
    search_fields = ('numero', 'client__nom')
    inlines = [LigneCommandeInline]
    readonly_fields = ('numero', 'total_ht', 'total_ttc', 'cree_par')

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('commande', 'montant', 'mode_paiement', 'date_paiement')
    list_filter = ('mode_paiement', 'date_paiement')
    readonly_fields = ('enregistre_par',)
