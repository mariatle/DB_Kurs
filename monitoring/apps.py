from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class MonitoringConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monitoring'

    def ready(self):
        # Импортируем здесь, чтобы избежать циклических импортов
        from django.conf import settings
        
        # 1. Регистрация сигналов для анализа данных
        self.register_signals()
        
        # 2. Запуск планировщика (только в DEBUG режиме)
        if settings.DEBUG:
            self.start_scheduler()

    def register_signals(self):
        """Регистрация обработчиков сигналов"""
        try:
            import monitoring.signals  # noqa
            logger.info("Сигналы успешно зарегистрированы")
        except Exception as e:
            logger.error(f"Ошибка регистрации сигналов: {e}")

    def start_scheduler(self):
        """Запуск фонового планировщика"""
        try:
            from monitoring.scheduler import start_scheduler
            start_scheduler()
            logger.info("Планировщик успешно запущен")
        except Exception as e:
            logger.error(f"Ошибка запуска планировщика: {e}")