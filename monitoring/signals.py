# monitoring/signals.py
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import AnalyzedInformation, Alarm, Incident, IncidentStatusHistory

logger = logging.getLogger(__name__)

# --- мгновенный анализ ENV убран — его делает Celery‑task ---

@receiver(post_save, sender=Alarm)
def handle_alarm_update(sender, instance, created, **kwargs):
    if instance.status == "resolved" and instance.incident:
        instance.incident.close_incident()


@receiver(post_save, sender=AnalyzedInformation)
def create_alarm_on_hazard(sender, instance, created, **kwargs):
    if not (created and instance.fire_hazard is not None):
        return

    if instance.fire_hazard >= 90:
        level = "critical"
    elif instance.fire_hazard >= 70:
        level = "high"
    elif instance.fire_hazard >= 50:
        level = "medium"
    else:
        return

    try:
        Alarm.objects.create(
            analysis=instance,
            alarm_level=level,
            status="active",
            alarm_at=timezone.now(),
        )
        logger.info("Создана тревога уровня %s", level)
    except Exception as e:
        logger.error("Ошибка создания тревоги: %s", e, exc_info=True)


@receiver(post_save, sender=Incident)
def create_initial_status_history(sender, instance, created, **kwargs):
    if created:
        IncidentStatusHistory.objects.create(
            incident=instance,
            new_status=instance.status,
            comment="Инцидент создан",
        )