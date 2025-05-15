# monitoring/tasks.py
import logging
import random
from datetime import timedelta

from celery import shared_task
from django.db import close_old_connections, transaction
from django.utils import timezone

from .models import (
    Device,
    EnvironmentalParameters,
    AnalyzedInformation,
)

logger = logging.getLogger(__name__)


# ───────────────────────────────────────────────────────────
# 1) генерация телеметрии – каждые 5 с (Celery Beat)
# ───────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def generate_random_data(self):
    """
    Создаёт по одной записи EnvironmentalParameters
    для каждого Device. Частота задаётся в CELERY_BEAT_SCHEDULE.
    """
    try:
        close_old_connections()
        now = timezone.now()

        devices = Device.objects.all().only("id")
        bulk = [
            EnvironmentalParameters(
                device_id=d.id,
                temperature=round(random.uniform(20, 50), 2),
                humidity=round(random.uniform(10, 90), 2),
                co2_level=round(random.uniform(300, 2000), 2),
                recorded_at=now,
            )
            for d in devices
        ]

        with transaction.atomic():
            EnvironmentalParameters.objects.bulk_create(bulk, ignore_conflicts=True)

        logger.info("ENV task: сгенерировано %s строк", len(bulk))

    except Exception as exc:
        logger.exception("ENV task error – retry через 5 с")
        raise self.retry(exc=exc)


# ───────────────────────────────────────────────────────────
# 2) batch‑анализ – каждые 5 с (Celery Beat)
#    Alarm создаёт сигнал post_save в signals.py
# ───────────────────────────────────────────────────────────
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def calculate_hazard_batch(self, batch_size: int = 1000):
    """
    Берёт непроцессed EnvironmentalParameters,
    рассчитывает fire_hazard и сохраняет AnalyzedInformation.
    Alarm далее создаётся сигналом create_alarm_on_hazard.
    """
    try:
        rows = (
            EnvironmentalParameters.objects
            .filter(processed=False)
            .order_by("id")[:batch_size]
        )
        if not rows:
            return  # нечего обрабатывать

        with transaction.atomic():
            for row in rows:
                hazard = AnalyzedInformation.calculate_fire_hazard(row)
                AnalyzedInformation.objects.create(
                    recorded_data=row,
                    fire_hazard=hazard,
                )
                row.processed = True   # помечаем
            EnvironmentalParameters.objects.bulk_update(rows, ["processed"])

        logger.info("Hazard batch: обработано %s ENV", len(rows))

    except Exception as exc:
        logger.exception("Hazard batch error – retry через 5 с")
        raise self.retry(exc=exc)


# ───────────────────────────────────────────────────────────
# 3) ежедневная чистка старых данных
# ───────────────────────────────────────────────────────────
@shared_task
def purge_old_env(days: int = 30):
    """
    Удаляет EnvironmentalParameters старше N дней.
    Запускается раз в сутки из Celery Beat.
    """
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = EnvironmentalParameters.objects.filter(
        recorded_at__lt=cutoff
    ).delete()
    logger.info("PURGE: удалено %s старых ENV", deleted)