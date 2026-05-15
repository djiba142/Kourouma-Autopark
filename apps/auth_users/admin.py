from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur

@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ('email', 'nom', 'role', 'actif', 'is_staff')
    list_filter = ('role', 'actif', 'is_staff')
    search_fields = ('email', 'nom', 'telephone')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'telephone')}),
        ('Permissions', {'fields': ('role', 'actif', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_creation')}),
    )
    readonly_fields = ('date_creation',)
