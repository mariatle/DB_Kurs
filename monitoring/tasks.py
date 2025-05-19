import random
import logging
from datetime import timedelta

from celery import shared_task
from django.db import close_old_connections, transaction
from django.utils import timezone

from .models import Device, EnvironmentalParameters, AnalyzedInformation

logger = logging.getLogger(__name__)

# ───────────────────────── 1) генерация ─────────────────────────
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def generate_random_data(self):
    """
    Создаёт по одной записи EnvironmentalParameters
    для каждого Device и сразу ставит задачу анализа.
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
                co2_level=round(random.uniform(300, 2000), 2),   # &larr; ТОЛЬКО co2_level
                recorded_at=now,
            )
            for d in devices
        ]
        EnvironmentalParameters.objects.bulk_create(bulk, ignore_conflicts=True)
        logger.info("ENV создано: %s", len(bulk))

        # сразу ставим анализ через 5 с
        calculate_hazard_batch.apply_async(countdown=5)

    except Exception as exc:
        logger.exception("ENV task error — retry через 5 с")
        raise self.retry(exc=exc)

# ───────────────────────── 2) анализ ────────────────────────────
# monitoring/tasks.py  – внутри calculate_hazard_batch

@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def calculate_hazard_batch(self, batch_size: int = 1000):
    try:
        rows = (EnvironmentalParameters.objects
                .filter(processed=False)
                .order_by("id")[:batch_size])
        if not rows:
            return

        with transaction.atomic():
            for row in rows:
                hazard = AnalyzedInformation.calculate_fire_hazard(row)

                # &darr; СОЗДАЁМ ОТДЕЛЬНО — сработает post_save &rarr; create_alarm_on_hazard
                AnalyzedInformation.objects.create(
                    recorded_data=row,
                    fire_hazard=hazard,
                )
                row.processed = True

            EnvironmentalParameters.objects.bulk_update(rows, ["processed"])

        logger.info("Hazard batch: обработано %s ENV", len(rows))

    except Exception as exc:
        logger.exception("Hazard batch error — retry через 5 с")
        raise self.retry(exc=exc)
# ───────────────────────── 3) чистка ────────────────────────────
@shared_task
def purge_old_env(days: int = 30):
    """
    Удаляет ТОЛЬКО те ENV, которые ещё не анализировались
    (processed=False и нет ссылки в AnalyzedInformation)
    и старше заданного порога.
    """
    cutoff = timezone.now() - timedelta(days=days)
    qs = (
        EnvironmentalParameters.objects
        .filter(recorded_at__lt=cutoff,
                processed=False,
                analyzedinformation__isnull=True)
    )
    deleted, _ = qs.delete()
    logger.info("PURGE: удалено %s сырых ENV", deleted)