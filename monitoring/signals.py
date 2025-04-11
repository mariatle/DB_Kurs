from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EnvironmentalParameters, AnalyzedInformation
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