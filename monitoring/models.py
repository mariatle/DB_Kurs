from django.db import models
from django.db.models.functions import TruncMinute, TruncHour, TruncDay
from django.db.models import Min, Avg, Max, Count

class Location(models.Model):
    location_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.location_name

    class Meta:
        db_table = "location"
        verbose_name_plural = "Location"


class Device(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    inventory_number = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=50, blank=True, null=True)
    date_of_installation = models.DateField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=6, blank=True, null=True)

    class Meta:
        db_table = "device"
        verbose_name_plural = "Device"


class EnvironmentalParameters(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    humidity = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    wind_speed = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    co2_level = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    recorded_at = models.DateTimeField()

    class Meta:
        db_table = "environmental_parameters"
        verbose_name_plural = "EnvironmentalParameters"


class AnalyzedInformation(models.Model):
    recorded_data = models.ForeignKey(EnvironmentalParameters, on_delete=models.CASCADE)
    fire_hazard = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    analyzed_at = models.DateTimeField()

    class Meta:
        db_table = "analyzed_information"
        verbose_name_plural = "AnalyzedInformation"


class Incident(models.Model):
    status = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    detected_at = models.DateTimeField()
    resolved_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "incident"
        verbose_name_plural = "Incident"


class Alarm(models.Model):
    analysis = models.ForeignKey(AnalyzedInformation, on_delete=models.CASCADE)
    # Можно оставить SET_NULL или поменять на CASCADE в зависимости от логики
    incident = models.ForeignKey(Incident, on_delete=models.SET_NULL, blank=True, null=True)
    status = models.CharField(max_length=50)
    alarm_level = models.CharField(max_length=20)
    alarm_at = models.DateTimeField()

    class Meta:
        db_table = "alarm"
        verbose_name_plural = "Alarm"