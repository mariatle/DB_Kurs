from rest_framework import serializers
from .models import (
    Location,
    Device,
    EnvironmentalParameters,
    AnalyzedInformation,
    Incident,
    Alarm
)


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'  # Или можно указать конкретные поля: ['id', 'location_name', 'description']


class DeviceSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)  # Вложенный сериализатор для локации
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source='location',
        write_only=True,
        required=True
    )

    class Meta:
        model = Device
        fields = '__all__'  # Или выбрать нужные поля


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