from datetime import timedelta

from django.utils import timezone
from django.db.models import Avg
from rest_framework import serializers

from .models import (
    Location,
    Device,
    EnvironmentalParameters,
    AnalyzedInformation,
    Incident,
    Alarm,
    IncidentStatusHistory
)



class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'  # Или можно указать конкретные поля: ['id', 'location_name', 'description']


# monitoring/serializers.py
class DeviceSerializer(serializers.ModelSerializer):
    # читаемая локация + write‑only FK
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="location",
        write_only=True,
        required=True,
    )

    # динамика для дашборда
    current_alarm = serializers.SerializerMethodField()
    avg_hazard_1h = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            "id",
            "inventory_number",
            "latitude",
            "longitude",
            "current_alarm",
            "avg_hazard_1h",
            "location",
            "location_id",
        ]
        read_only_fields = ("current_alarm", "avg_hazard_1h", "location")

    # ───── helpers ────────────────────────────────────────────
    def get_current_alarm(self, obj):
        level = (
            obj.environmentalparameters_set.filter(
                analyzedinformation__alarms__status="active"
            )
            .order_by("-analyzedinformation__alarms__alarm_at")
            .values_list("analyzedinformation__alarms__alarm_level", flat=True)
            .first()
        )
        return level or "low"

    def get_avg_hazard_1h(self, obj):
        cutoff = timezone.now() - timedelta(hours=1)
        val = (
            AnalyzedInformation.objects.filter(
                recorded_data__device=obj, analyzed_at__gte=cutoff
            ).aggregate(avg=Avg("fire_hazard"))["avg"]
        )
        return round(val or 0, 1)

class EnvironmentalParametersSerializer(serializers.ModelSerializer):
    device = DeviceSerializer(read_only=True)  # Вложенный сериализатор для устройства
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source='device',
        write_only=True,
        required=True
    )

    class Meta:
        model = EnvironmentalParameters
        fields = '__all__'


class AnalyzedInformationSerializer(serializers.ModelSerializer):
    recorded_data = EnvironmentalParametersSerializer(read_only=True)  # Вложенные данные
    recorded_data_id = serializers.PrimaryKeyRelatedField(
        queryset=EnvironmentalParameters.objects.all(),
        source='recorded_data',
        write_only=True,
        required=True
    )

    class Meta:
        model = AnalyzedInformation
        fields = '__all__'


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Incident
        fields = '__all__'


class AlarmSerializer(serializers.ModelSerializer):
    analysis = AnalyzedInformationSerializer(read_only=True)  # Вложенные данные анализа
    analysis_id = serializers.PrimaryKeyRelatedField(
        queryset=AnalyzedInformation.objects.all(),
        source='analysis',
        write_only=True,
        required=True
    )
    
    incident = IncidentSerializer(read_only=True)  # Вложенные данные инцидента
    incident_id = serializers.PrimaryKeyRelatedField(
        queryset=Incident.objects.all(),
        source='incident',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = Alarm
        fields = '__all__'
        
class TimeLocationGroupedSerializer(serializers.Serializer):
    location_id = serializers.IntegerField()
    location_name = serializers.CharField()
    time_period = serializers.DateTimeField()  # Для минут/часов
    date = serializers.DateField()            # Для дней/недель
    avg_temperature = serializers.DecimalField(max_digits=5, decimal_places=2)
    max_co2 = serializers.DecimalField(max_digits=10, decimal_places=2)
    hazard_index = serializers.DecimalField(max_digits=5, decimal_places=2)
    device_count = serializers.IntegerField()
    
    
    
# serializers.py
class IncidentStatusHistorySerializer(serializers.ModelSerializer):
    changed_by = serializers.StringRelatedField()  # Или UserSerializer, если есть
    
    class Meta:
        model = IncidentStatusHistory
        fields = '__all__'
        read_only_fields = ('changed_at',)