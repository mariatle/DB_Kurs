# monitoring/admin.py
from django.contrib import admin
from django.utils import timezone

from .models import (
    Location,
    Device,
    EnvironmentalParameters,
    AnalyzedInformation,
    Alarm,
    Incident,
)

# ──────────────────────────
# Базовые модели
# ──────────────────────────
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("id", "location_name", "description")
    search_fields = ("location_name",)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("id", "inventory_number", "location", "type", "date_of_installation")
    list_filter = ("location", "type")
    search_fields = ("inventory_number",)


@admin.register(EnvironmentalParameters)
class EnvironmentalParametersAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "device",
        "temperature",
        "humidity",
        "co2_level",
        "recorded_at",
        "processed",
    )
    list_filter = ("device__location", "device")
    readonly_fields = ("recorded_at",)


@admin.register(AnalyzedInformation)
class AnalyzedInformationAdmin(admin.ModelAdmin):
    list_display = ("id", "recorded_data", "fire_hazard", "analyzed_at")
    list_filter = ("recorded_data__device__location",)
    readonly_fields = ("analyzed_at",)


@admin.register(Alarm)
class AlarmAdmin(admin.ModelAdmin):
    list_display = ("id", "alarm_level", "status", "incident", "alarm_at")
    list_filter = ("alarm_level", "status", "incident__location")
    readonly_fields = ("alarm_at",)


# ──────────────────────────
# Инциденты
# ──────────────────────────
@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "display_location", "time_window", "status", "alarms_count")
    list_filter = ("status", "location")
    readonly_fields = (
        "time_window_start",
        "time_window_end",
        "detected_at",
        "resolved_at",
    )

    # ── Локация ────────────────────────────
    def display_location(self, obj):
        return obj.location.location_name if obj.location else "Не указана"

    display_location.short_description = "Локация"

    # ── Временное окно ─────────────────────
    def time_window(self, obj):
        start = timezone.localtime(obj.time_window_start)
        end = timezone.localtime(obj.time_window_end) if obj.time_window_end else None
        return f"{start:%H:%M} – {end:%H:%M}" if end else f"{start:%H:%M} – …"

    time_window.short_description = "Временное окно"

    # ── Кол‑во тревог ──────────────────────
    def alarms_count(self, obj):
        return obj.alarms.count()

    alarms_count.short_description = "Кол-во тревог"