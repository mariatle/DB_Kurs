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
        'display_location',  # Изменили название метода
        'time_window',
        'status',
        'alarms_count'
    )
    
    def display_location(self, obj):
        return obj.location.location_name if obj.location else "Не указана"
    display_location.short_description = 'Локация'
    
    def time_window(self, obj):
        return f"{obj.time_window_start:%H:%M} – {obj.time_window_end:%H:%M}" if obj.time_window_end else "Активно"
    time_window.short_description = 'Временное окно'
    
    def alarms_count(self, obj):
        return obj.alarms.count()
    alarms_count.short_description = 'Кол-во тревог'