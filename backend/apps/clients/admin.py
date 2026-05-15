from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'telephone', 'email', 'score_statut', 'actif')
    list_filter = ('score_statut', 'actif')
    search_fields = ('nom', 'telephone', 'email')
