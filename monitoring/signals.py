from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EnvironmentalParameters, AnalyzedInformation, Alarm
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=EnvironmentalParameters)
def analyze_environmental_data(sender, instance, created, **kwargs):
    if created:  # Только для новых записей
        try:
            fire_hazard = AnalyzedInformation.calculate_fire_hazard(instance)
            
            AnalyzedInformation.objects.create(
                recorded_data=instance,
                fire_hazard=fire_hazard,
                analyzed_at=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            
@receiver(post_save, sender=Alarm)
def handle_alarm_update(sender, instance, created, **kwargs):
    if instance.status == 'resolved' and instance.incident:
        instance.incident.close_incident()
        
@receiver(post_save, sender=AnalyzedInformation)
def create_alarm_on_hazard(sender, instance, created, **kwargs):
    logger.info(f"Сигнал получен: created={created}, fire_hazard={instance.fire_hazard}")
    
    if created and instance.fire_hazard is not None:
        try:
            logger.debug(f"Расчет уровня тревоги для fire_hazard={instance.fire_hazard}")
            
            if instance.fire_hazard >= 90:
                level = 'critical'
            elif instance.fire_hazard >= 70:
                level = 'high'
            elif instance.fire_hazard >= 50:
                level = 'medium'
            else:
                logger.info("Уровень опасности ниже порогового значения")
                return

            logger.info(f"Попытка создания тревоги уровня {level}")
            Alarm.objects.create(
                analysis=instance,
                alarm_level=level,
                status='active',
                alarm_at=timezone.now()
            )
            logger.info(f"Тревога успешно создана")

        except Exception as e:
            logger.error(f"Ошибка создания тревоги: {str(e)}", exc_info=True)