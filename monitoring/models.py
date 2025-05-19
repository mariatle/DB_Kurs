# monitoring/models.py
import logging
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model


def get_system_user():
    """
    Возвращает специального пользователя `system`
    (создайте его один раз через createsuperuser).
    """
    return get_user_model().objects.get(username="system")

logger = logging.getLogger(__name__)
User = get_user_model()


# ──────────────────────────
#  Справочники
# ──────────────────────────
class Location(models.Model):
    location_name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "location"
        verbose_name_plural = "Location"

    def __str__(self):
        return self.location_name


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

    def __str__(self):
        return self.inventory_number


# ──────────────────────────
#  Сырая телеметрия
# ──────────────────────────
# monitoring/models.py  (фрагмент)

from django.db import models
from django.db.models import Q
from django.utils import timezone

class EnvironmentalParameters(models.Model):
    device       = models.ForeignKey(Device, on_delete=models.CASCADE)
    temperature  = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    humidity     = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    co2_level    = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    recorded_at  = models.DateTimeField(default=timezone.now)
    processed    = models.BooleanField(default=False)

    class Meta:
        db_table = "environmental_parameters"
        verbose_name_plural = "EnvironmentalParameters"

        # ─── новые индексы ──────────────────────────────────────
        indexes = [
            # 1) составной: ускоряет сортировку последних записей по устройству
            models.Index(
                fields=["device", "recorded_at"],
                name="env_dev_rec_idx",
            ),
            # 2) частичный: &laquo;живой хвост&raquo; только необработанных строк
            models.Index(
                fields=["recorded_at"],
                name="env_processed_false_idx",
                condition=Q(processed=False),
            ),
        ]

        # 旧 Check‑constraints оставляем без изменений
        constraints = [
            models.CheckConstraint(
                check=Q(temperature__gte=-50, temperature__lte=200),
                name="chk_env_temp",
            ),
            models.CheckConstraint(
                check=Q(humidity__gte=0, humidity__lte=100),
                name="chk_env_humidity",
            ),
            models.CheckConstraint(check=Q(co2_level__gte=0), name="chk_env_co2"),
        ]

    def __str__(self):
        local_ts = timezone.localtime(self.recorded_at)
        return f"{self.device} @ {local_ts:%Y-%m-%d %H:%M:%S}"

# ──────────────────────────
#  Анализ
# ──────────────────────────
class AnalyzedInformation(models.Model):
    recorded_data = models.ForeignKey(
        EnvironmentalParameters, on_delete=models.CASCADE, verbose_name="Исходные данные"
    )
    fire_hazard = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Уровень пожарной опасности",
        null=True,
        blank=True,
    )
    analyzed_at = models.DateTimeField(auto_now_add=True, verbose_name="Время анализа")

    class Meta:
        db_table = "analyzed_information"
        verbose_name_plural = "Analyzed information"
        ordering = ["-analyzed_at"]

    def __str__(self):
        return f"Анализ #{self.id} (Опасность: {self.fire_hazard}%)"

    @classmethod
    def calculate_fire_hazard(cls, env_data):
        try:
            temp = Decimal(str(env_data.temperature or 0))
            humidity = Decimal(str(env_data.humidity or 0))
            co2 = Decimal(str(env_data.co2_level or 0))

            temp_factor = max(Decimal("0"), (temp - Decimal("15")) / Decimal("25"))
            humidity_factor = max(
                Decimal("0"), (Decimal("30") - humidity) / Decimal("30")
            )
            co2_factor = min(Decimal("1"), co2 / Decimal("2000"))

            hazard = (
                temp_factor * Decimal("0.6")
                + humidity_factor * Decimal("0.3")
                + co2_factor * Decimal("0.1")
            ) * Decimal("100")

            return min(
                Decimal("100"), max(Decimal("0"), hazard.quantize(Decimal("0.01")))
            )
        except Exception as e:
            logger.error(f"Ошибка расчёта опасности: {e}")
            return None


# ──────────────────────────
#  Incidents & Alarms
# ──────────────────────────
class Incident(models.Model):
    STATUS_CHOICES = [
        ("open", "Открыт"),
        ("investigation", "Расследование"),
        ("resolved", "Решён"),
        ("closed", "Закрыт"),
    ]

    location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Локация",
    )
    time_window_start = models.DateTimeField(default=timezone.now, verbose_name="Начало")
    time_window_end = models.DateTimeField(blank=True, null=True, verbose_name="Конец")
    detected_at = models.DateTimeField(auto_now_add=True, verbose_name="Обнаружен")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name="Закрыт")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="open", verbose_name="Статус"
    )

    class Meta:
        ordering = ["-detected_at"]

    # —— запоминаем исходный статус ——
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_status = self.status

    # —— аудит при любом сохранении ——
    def save(self, *args, **kwargs):
        changed_by = kwargs.pop("changed_by", None)
        comment = kwargs.pop("comment", None)

        if self.pk and self._original_status != self.status:
            IncidentStatusHistory.objects.create(
                incident=self,
                old_status=self._original_status,
                new_status=self.status,
                changed_by=changed_by,
                comment=comment,
            )

        super().save(*args, **kwargs)
        self._original_status = self.status  # обновляем &laquo;оригинал&raquo;

    # —— метод для скриптов / action-кнопок ——
    def change_status(self, new_status, user=None, comment=None):
        # если вызвали без указания пользователя &rarr; берём системного
        if user is None:
            user = get_system_user()

        if new_status not in dict(self.STATUS_CHOICES):
            raise ValueError(f"Invalid status: {new_status}")

        if self.status == new_status:
            return False

        self.status = new_status
        if new_status == "closed":
            self.resolved_at = timezone.now()

        # передаём пользователя дальше — save() создаст history
        self.save(changed_by=user, comment=comment)
        return True


    def close_incident(self, user=None, comment=None):
        if self.status not in ["closed", "resolved"] and not self.alarms.filter(status="active").exists():
            return self.change_status(
                "closed", user, comment or "Автоматическое закрытие"
            )
        return False

    def __str__(self):
        return f"Incident #{self.id} ({self.get_status_display()})"


class IncidentStatusHistory(models.Model):
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name="status_history",
        verbose_name="Инцидент",
    )
    old_status = models.CharField(
        max_length=20,
        choices=Incident.STATUS_CHOICES,
        blank=True,
        null=True,
        verbose_name="Старый статус",
    )
    new_status = models.CharField(
        max_length=20, choices=Incident.STATUS_CHOICES, verbose_name="Новый статус"
    )
    changed_at = models.DateTimeField(auto_now_add=True, verbose_name="Время смены")
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Кем изменён",
    )
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")

    class Meta:
        db_table = "incident_status_history"
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.incident_id}: {self.old_status} &rarr; {self.new_status}"


class Alarm(models.Model):
    STATUS_CHOICES = [
        ("active", "Активна"),
        ("acknowledged", "Подтверждена"),
        ("resolved", "Решена"),
    ]
    ALARM_LEVELS = [
        ("low", "Низкий"),
        ("medium", "Средний"),
        ("high", "Высокий"),
        ("critical", "Критический"),
    ]

    analysis = models.ForeignKey(
        AnalyzedInformation,
        on_delete=models.PROTECT,
        related_name="alarms",
        verbose_name="Анализ",
    )
    incident = models.ForeignKey(
        Incident,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="alarms",
        verbose_name="Инцидент",
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active", verbose_name="Статус"
    )
    alarm_level = models.CharField(
        max_length=20, choices=ALARM_LEVELS, verbose_name="Уровень"
    )
    alarm_at = models.DateTimeField(verbose_name="Время")

    class Meta:
        db_table = "alarm"
        ordering = ["-alarm_at"]
        indexes = [models.Index(fields=["status", "alarm_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["analysis", "alarm_level"],
                name="uniq_alarm_analysis_level",
            ),
        ]

    # —— бизнес-логика ——
    def trigger_alarm(self):
        if self.alarm_level not in ["high", "critical"] or self.status != "active":
            return
        location = self.analysis.recorded_data.device.location
        window_start = timezone.now() - timedelta(hours=2)

        incident = (
            Incident.objects.filter(
                location=location,
                time_window_start__gte=window_start,
                status__in=["open", "investigation"],
            )
            .order_by("-time_window_start")
            .first()
        )

        if incident:
            self.incident = incident
            incident.time_window_end = timezone.now()
            incident.save(update_fields=["time_window_end"])
        else:
            incident = Incident.objects.create(
                location=location,
                time_window_start=timezone.now(),
                status="open",
                description=f"Автоматически создан для тревоги {self.id}",
            )
            self.incident = incident

        super().save(update_fields=["incident"])
        logger.info("Alarm %s linked to incident %s", self.id, self.incident_id)

    # —— валидация ——
    def clean(self):
        if self.alarm_at > timezone.now():
            raise ValidationError("Время тревоги не может быть в будущем")
        if self.incident and self.incident.status == "closed":
            raise ValidationError("Нельзя привязывать к закрытому инциденту")

    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.status == "active":
            self.trigger_alarm()

    def __str__(self):
        return f"Alarm #{self.id} - {self.get_alarm_level_display()} ({self.get_status_display()})"
    