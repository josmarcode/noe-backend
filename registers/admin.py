from django.contrib import admin
from .models import Register

@admin.register(Register)
class RegisterAdmin(admin.ModelAdmin):
    list_display  = ['id', 'tracker', 'kilometers', 'amount', 'tracker_at', 'is_active']
    list_filter   = ['is_active', 'tracker__type']
    search_fields = ['note', 'tracker__name']
    ordering      = ['-tracker_at']
