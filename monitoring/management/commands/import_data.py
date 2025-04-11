import json
import os
from django.conf import settings
from django.core.management.base import BaseCommand
from monitoring.models import *

class Command(BaseCommand):
    help = 'Импорт данных из JSON'
    
    def get_data_path(self, filename):
        return os.path.join(settings.BASE_DIR, 'data', filename)

    def handle(self, *args, **kwargs):
        try:
            # Порядок импорта важен!
            self.import_locations()
            self.import_devices()
            self.import_environmental()
            self.import_analyzed()
            self.import_incidents()
            self.import_alarms()
            self.stdout.write(self.style.SUCCESS('✅ Все данные импортированы!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Фатальная ошибка: {str(e)}'))

    # Методы для каждой модели
    def import_locations(self):
        self._import_model(
            model=Location,
            filename='location.json'
        )

    def import_devices(self):
        self._import_model(
            model=Device,
            filename='device.json',
            fixer=self.fix_device
        )

    def import_environmental(self):
        self._import_model(
            model=EnvironmentalParameters,
            filename='environmental_parameters.json',
            fixer=self.fix_environmental
        )

    def import_analyzed(self):
        self._import_model(
            model=AnalyzedInformation,
            filename='analyzed_information.json',
            fixer=self.fix_analyzed
        )

    def import_incidents(self):
        self._import_model(
            model=Incident,
            filename='incident.json'
        )

    def import_alarms(self):
        self._import_model(
            model=Alarm,
            filename='alarm.json',
            fixer=self.fix_alarm
        )

    # Общий метод импорта
    def _import_model(self, model, filename, fixer=None):
        try:
            path = self.get_data_path(filename)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Файл {filename} не найден")
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    if fixer:
                        item = fixer(item)
                    model.objects.create(**item)
                self.stdout.write(self.style.SUCCESS(f'✅ {model.__name__} импортированы'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка в {model.__name__}: {str(e)}'))

    # Обработчики связей
    def fix_device(self, item):
        item['location'] = Location.objects.get(id=item['location'])
        return item

    def fix_environmental(self, item):
        item['device'] = Device.objects.get(id=item['device'])
        return item

    def fix_analyzed(self, item):
        item['recorded_data'] = EnvironmentalParameters.objects.get(id=item['recorded_data'])
        return item

    def fix_alarm(self, item):
        item['analysis'] = AnalyzedInformation.objects.get(id=item['analysis'])
        item['incident'] = Incident.objects.get(id=item['incident'])
        return item