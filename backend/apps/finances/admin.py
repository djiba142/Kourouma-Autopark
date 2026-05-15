from django.contrib import admin
from .models import CategorieDepense, Depense, JournalFinancier, CompteComptable, EcritureComptable

@admin.register(CategorieDepense)
class CategorieDepenseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'budget_mensuel')
    search_fields = ('nom',)

@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    list_display = ('numero', 'description', 'categorie', 'montant', 'devise', 'date_depense')
    list_filter = ('categorie', 'type_depense', 'devise', 'date_depense')
    search_fields = ('numero', 'description')
    readonly_fields = ('numero', 'montant_gnf', 'cree_par')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.cree_par = request.user
        super().save_model(request, obj, form, change)

@admin.register(JournalFinancier)
class JournalFinancierAdmin(admin.ModelAdmin):
    list_display = ('numero', 'date', 'type_operation', 'reference_doc', 'montant_gnf', 'type_flux')
    list_filter = ('type_operation', 'type_flux', 'date')
    search_fields = ('numero', 'reference_doc', 'description')
    readonly_fields = ('numero', 'date', 'type_operation', 'reference_doc', 'description', 
                       'montant', 'devise', 'taux', 'montant_gnf', 'type_flux', 'utilisateur')

@admin.register(CompteComptable)
class CompteComptableAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'type')
    list_filter = ('type',)
    search_fields = ('code', 'nom')

@admin.register(EcritureComptable)
class EcritureComptableAdmin(admin.ModelAdmin):
    list_display = ('journal', 'compte', 'debit', 'credit')
    list_filter = ('compte',)
