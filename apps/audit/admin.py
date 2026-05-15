from django.contrib import admin
from .models import AuditLog

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'utilisateur', 'action', 'ip')
    list_filter = ('type_action', 'date')
    search_fields = ('utilisateur__nom', 'utilisateur__email', 'action', 'details')
    readonly_fields = ('date', 'date_evenement', 'utilisateur', 'action', 'details', 'ip', 'type_action', 'description', 'ip_adresse')
