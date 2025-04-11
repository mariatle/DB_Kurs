from django.db import models
from django.db.models.functions import TruncMinute, TruncHour, TruncDay
from django.db.models import Min, Avg, Max, Count
from django.utils import timezone
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

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
    recorded_data = models.ForeignKey(
        'EnvironmentalParameters', 
        on_delete=models.CASCADE,
        verbose_name="Исходные данные"
    )
    fire_hazard = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name="Уровень пожарной опасности",
        null=True,
        blank=True
    )
    analyzed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Время анализа"
    )

    class Meta:
        db_table = "analyzed_information"
        verbose_name = "Анализ данных"
        verbose_name_plural = "Analyzed information"
        ordering = ['-analyzed_at']

    def __str__(self):
        return f"Анализ #{self.id} (Опасность: {self.fire_hazard}%)"

    @classmethod
    def calculate_fire_hazard(cls, env_data):
        """
        Усовершенствованная формула расчета пожарной опасности
        Возвращает значение от 0 (нет опасности) до 100 (критическая опасность)
        """
        try:
            # Конвертируем все входные значения в Decimal
            temp = Decimal(str(env_data.temperature))
            humidity = Decimal(str(env_data.humidity))
            co2 = Decimal(str(env_data.co2_level))
            wind = Decimal(str(env_data.wind_speed))
            
            # Нормализация параметров (используем Decimal для всех операций)
            temp_factor = max(Decimal('0'), (temp - Decimal('15')) / Decimal('25'))
            humidity_factor = max(Decimal('0'), (Decimal('30') - humidity) / Decimal('30'))
            co2_factor = min(Decimal('1'), co2 / Decimal('2000'))
            wind_factor = min(Decimal('1'), wind / Decimal('15'))
            
            # Весовые коэффициенты (в Decimal)
            weights = {
                'temperature': Decimal('0.5'),
                'humidity': Decimal('0.3'),
                'co2': Decimal('0.15'),
                'wind': Decimal('0.05')
            }
            
            # Расчет итогового значения
            hazard = (
                temp_factor * weights['temperature'] +
                humidity_factor * weights['humidity'] +
                co2_factor * weights['co2'] +
                wind_factor * weights['wind']
            ) * Decimal('100')  # Приведение к процентной шкале
            
            return min(Decimal('100'), max(Decimal('0'), round(hazard, 2)))
            
        except Exception as e:
            logger.error(f"Ошибка расчета опасности: {e}")
            return None




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