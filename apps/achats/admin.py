from django.contrib import admin
from .models import Fournisseur, CommandeAchat, LigneAchat

@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays', 'type', 'devise_par_defaut', 'actif')
    list_filter = ('type', 'actif', 'pays')
    search_fields = ('nom', 'email')

class LigneAchatInline(admin.TabularInline):
    model = LigneAchat
    extra = 0

@admin.register(CommandeAchat)
class CommandeAchatAdmin(admin.ModelAdmin):
    list_display = ('reference', 'fournisseur', 'statut', 'total_gnf', 'date_commande')
    list_filter = ('statut', 'fournisseur', 'date_commande')
    search_fields = ('reference', 'notes')
    inlines = [LigneAchatInline]
    readonly_fields = ('reference', 'total_devise', 'total_gnf', 'cree_par')
