from django.contrib import admin
from .models import Lead

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('sl', 'lead_id', 'customer_name', 'mobile', 'lead_type', 'followup', 'associate')
    list_filter = ('lead_type', 'associate', 'team_leader')
    search_fields = ('customer_name', 'mobile', 'lead_id')
    readonly_fields = ('lead_id',)  # Prevent editing lead_id