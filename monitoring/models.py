# models.py
from django.db import models
from django.db.models.functions import TruncMinute, TruncHour, TruncDay
from django.db.models import Min, Avg, Max, Count
from django.forms import ValidationError
from django.utils import timezone
import logging
from decimal import Decimal
from datetime import timedelta

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
        """Расчет уровня пожарной опасности"""
        try:
            temp = Decimal(str(env_data.temperature))
            humidity = Decimal(str(env_data.humidity))
            co2 = Decimal(str(env_data.co2_level))
            wind = Decimal(str(env_data.wind_speed))
            
            temp_factor = max(Decimal('0'), (temp - Decimal('15')) / Decimal('25'))
            humidity_factor = max(Decimal('0'), (Decimal('30') - humidity) / Decimal('30'))
            co2_factor = min(Decimal('1'), co2 / Decimal('2000'))
            wind_factor = min(Decimal('1'), wind / Decimal('15'))
            
            weights = {
                'temperature': Decimal('0.5'),
                'humidity': Decimal('0.3'),
                'co2': Decimal('0.15'),
                'wind': Decimal('0.05')
            }
            
            hazard = (
                temp_factor * weights['temperature'] +
                humidity_factor * weights['humidity'] +
                co2_factor * weights['co2'] +
                wind_factor * weights['wind']
            ) * Decimal('100')
            
            return min(Decimal('100'), max(Decimal('0'), round(hazard, 2)))
            
        except Exception as e:
            logger.error(f"Ошибка расчета опасности: {e}")
            return None


class Incident(models.Model):
    location = models.ForeignKey(
        'Location',  # Используем строку, чтобы избежать циклических импортов
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Локация'
    )
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('investigation', 'Расследование'),
        ('resolved', 'Решен'),
        ('closed', 'Закрыт'),
    ]
    # Оставляем текущий статус, но удаляем resolved_at (будет храниться в истории)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        verbose_name='Текущий статус'
    )
    
    # Добавляем метод для изменения статуса
    def change_status(self, new_status, user=None, comment=None):
        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")
            
        if self.status == new_status:
            return False
            
        # Создаем запись в истории
        IncidentStatusHistory.objects.create(
            incident=self,
            old_status=self.status,
            new_status=new_status,
            changed_by=user,
            comment=comment
        )
        
        # Обновляем текущий статус
        self.status = new_status
        
        # Если инцидент закрывается, обновляем время решения
        if new_status == 'closed':
            self.resolved_at = timezone.now()
            
        self.save()
        return True

    # Модифицируем метод close_incident
    def close_incident(self, user=None, comment=None):
        if self.status not in ['closed', 'resolved']:
            has_unresolved = self.alarms.filter(status='active').exists()
            
            if not has_unresolved:
                return self.change_status('closed', user, comment or "Автоматическое закрытие")
        return False

# models.py
from django.contrib.auth import get_user_model

User = get_user_model()

class IncidentStatusHistory(models.Model):
    STATUS_CHOICES = [
        ('open', 'Открыт'),
        ('investigation', 'Расследование'),
        ('resolved', 'Решен'),
        ('closed', 'Закрыт'),
    ]
    
    incident = models.ForeignKey(
        'Incident',
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name='Инцидент'
    )
    old_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name='Предыдущий статус'
    )
    new_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='Новый статус'
    )
    changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Время изменения'
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Кто изменил'
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name='Комментарий'
    )

    class Meta:
        db_table = "incident_status_history"
        verbose_name = "История статуса инцидента"
        verbose_name_plural = "Истории статусов инцидентов"
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.incident.id}: {self.old_status} → {self.new_status}"


class Alarm(models.Model):
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('acknowledged', 'Подтверждена'),
        ('resolved', 'Решена'),
    ]
    
    ALARM_LEVELS = [
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('critical', 'Критический'),
    ]
    
    analysis = models.ForeignKey(
        AnalyzedInformation,
        on_delete=models.CASCADE,
        related_name='alarms',
        verbose_name='Анализ данных'
    )
    incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='alarms',
        verbose_name='Связанный инцидент'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='Статус тревоги'
    )
    alarm_level = models.CharField(
        max_length=20,
        choices=ALARM_LEVELS,
        verbose_name='Уровень тревоги'
    )
    alarm_at = models.DateTimeField(
        verbose_name='Время активации'
    )

    class Meta:
        db_table = "alarm"
        verbose_name = "Тревога"
        verbose_name_plural = "Alarm"
        indexes = [
            models.Index(fields=['status', 'alarm_at']),
        ]
        ordering = ['-alarm_at']

    def trigger_alarm(self):
        """Обработка тревоги и создание инцидента"""
        logger.info(f"Обработка тревоги {self.id} (уровень: {self.alarm_level})")
        if self.alarm_level in ['high', 'critical'] and self.status == 'active':
            try:
                location = self.analysis.recorded_data.device.location
                time_threshold = timezone.now() - timedelta(hours=2)
                
                incident = Incident.objects.filter(
                    location=location,
                    time_window_start__gte=time_threshold,
                    status__in=['open', 'investigation']
                ).order_by('-time_window_start').first()

                if incident:
                    self.incident = incident
                    incident.time_window_end = timezone.now()
                    incident.save(update_fields=['time_window_end'])
                else:
                    self.incident = Incident.objects.create(
                        location=location,
                        time_window_start=timezone.now(),
                        status='open',
                        detected_at=timezone.now(),
                        description=f"Автоматически создан для тревоги {self.id}"
                    )
                
                self.save()
                logger.info(f"Тревога {self.id} привязана к инциденту {self.incident.id}")

            except Exception as e:
                logger.error(f"Ошибка создания инцидента: {str(e)}", exc_info=True)

    def clean(self):
        if self.alarm_at > timezone.now():
            raise ValidationError("Время тревоги не может быть в будущем")
        
        if self.incident and self.incident.status == 'closed':
            raise ValidationError("Нельзя привязывать к закрытому инциденту")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        if self.status == 'active':
            self.trigger_alarm()

    def __str__(self):
        return f"Тревога #{self.id} - {self.get_alarm_level_display()} ({self.get_status_display()})"