from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'

    def ready(self):
        # Импортируем здесь, чтобы избежать циклических импортов
        from django.conf import settings
        
        if settings.DEBUG:
            try:
                from monitoring.scheduler import start_scheduler
                start_scheduler()
                logger.info("Планировщик успешно запущен")
            except Exception as e:
                logger.error(f"Ошибка запуска планировщика: {e}")