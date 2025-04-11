import random
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from monitoring.models import EnvironmentalParameters, Device
from django.utils import timezone
import logging
from django.db import close_old_connections

logger = logging.getLogger(__name__)

def generate_random_data():
    """Генерирует случайные данные для EnvironmentalParameters"""
    try:
        close_old_connections()  # Закрываем старые соединения с БД
        devices = Device.objects.all()
        
        for device in devices:
            EnvironmentalParameters.objects.create(
                device=device,
                temperature=round(random.uniform(-10, 35), 2),
                humidity=round(random.uniform(0, 100), 2),
                wind_speed=round(random.uniform(0, 20), 2),
                co2_level=round(random.uniform(300, 2000), 2),
                recorded_at=timezone.now()
            )
        logger.info(f"Сгенерированы новые данные в {timezone.now()}")
    except Exception as e:
        logger.error(f"Ошибка генерации данных: {e}")
    finally:
        close_old_connections()

def start_scheduler():
    try:
        scheduler = BackgroundScheduler()
        scheduler.add_jobstore(DjangoJobStore(), "default")
        
        scheduler.add_job(
            generate_random_data,
            'interval',
            minutes=20,
            id="env_data_generator",
            replace_existing=True
        )
        
        logger.info("Запуск планировщика...")
        scheduler.start()
    except Exception as e:
        logger.error(f"Ошибка планировщика: {e}")