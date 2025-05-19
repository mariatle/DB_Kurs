# monitoring/apps.py
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class MonitoringConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "monitoring"

    def ready(self):
        """
        При старте регистрируем только Django‑signals.
        Планировщик APScheduler убран — задачи выполняет Celery Beat.
        """
        self.register_signals()

    def register_signals(self):
        try:
            import monitoring.signals  # noqa
            logger.info("Сигналы успешно зарегистрированы")
        except Exception as exc:
            logger.error("Ошибка регистрации сигналов: %s", exc)
            