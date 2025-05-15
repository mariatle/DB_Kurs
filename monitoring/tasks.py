# monitoring/tasks.py
import logging
import random
from datetime import datetime, timedelta

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
@shared_task
def generate_random_data():
    """Генерирует случайные параметры среды для всех устройств."""
    # Список идентификаторов устройств (пример)
    devices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    data = [
        EnvironmentalParameters(
            device_id=device,
            temperature=random.uniform(15, 35),
            humidity=random.uniform(30, 80),
            co2=random.uniform(300, 600),
            recorded_at=datetime.now()
        )
        for device in devices
    ]
    
    # Сохраняем пачкой для производительности
    EnvironmentalParameters.objects.bulk_create(data)
    logger.info("ENV создано: %s", len(data))

    # Сразу вызываем анализ с задержкой в 5 секунд
    calculate_hazard_batch.apply_async(countdown=5)


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
    