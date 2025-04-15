from django.contrib import admin
from .models import *

admin.site.register(Location)
admin.site.register(Device)
admin.site.register(EnvironmentalParameters)
admin.site.register(AnalyzedInformation)

admin.site.register(Alarm)

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'location', 
        'time_window', 
        'status', 
        'alarms_count'
    )
    
    def time_window(self, obj):
        return f"{obj.time_window_start:%H:%M} – {obj.time_window_end:%H:%M}" if obj.time_window_end else "Активно"
    
    def alarms_count(self, obj):
        return obj.alarms.count()