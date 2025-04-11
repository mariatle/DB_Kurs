from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg, Max, Min, Count
from django.db.models.functions import TruncHour, TruncDay
from django.db.models import F
from django.utils import timezone
from datetime import timedelta
from .models import (
    Location,
    Device,
    EnvironmentalParameters,
    AnalyzedInformation,
    Incident,
    Alarm
)
from .serializers import (
    LocationSerializer,
    DeviceSerializer,
    EnvironmentalParametersSerializer,
    AnalyzedInformationSerializer,
    IncidentSerializer,
    AlarmSerializer,
    TimeLocationGroupedSerializer
)

# Стандартные ViewSets для всех моделей
class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

class EnvironmentalParametersViewSet(viewsets.ModelViewSet):
    queryset = EnvironmentalParameters.objects.all()
    serializer_class = EnvironmentalParametersSerializer

class AnalyzedInformationViewSet(viewsets.ModelViewSet):
    queryset = AnalyzedInformation.objects.all()
    serializer_class = AnalyzedInformationSerializer

class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer

class AlarmViewSet(viewsets.ModelViewSet):
    queryset = Alarm.objects.all()
    serializer_class = AlarmSerializer

# Кастомный View для группировки данных
class TimeLocationGroupedView(APIView):
    """
    Группировка данных по локациям и временным промежуткам
    Поддерживаемые параметры:
    - range: hour/day/week/month (по умолчанию day)
    - location_id: фильтр по конкретной локации
    - days: количество дней для анализа (альтернатива range)
    """
    
    def get(self, request):
        # Параметры запроса
        time_range = request.query_params.get('range', 'day').lower()
        location_id = request.query_params.get('location_id')
        days = int(request.query_params.get('days', 0))
        
        # Определяем временной отрезок
        if days > 0:
            time_filter = timedelta(days=days)
            trunc_function = TruncDay
        else:
            time_filter = {
                'hour': timedelta(hours=1),
                'day': timedelta(days=1),
                'week': timedelta(weeks=1),
                'month': timedelta(days=30),
            }.get(time_range, timedelta(days=1))
            
            trunc_function = {
                'hour': TruncHour,
                'day': TruncDay,
                'week': TruncDay,
                'month': TruncDay,
            }.get(time_range, TruncDay)
        
        # Базовый запрос
        queryset = EnvironmentalParameters.objects.filter(
            recorded_at__gte=timezone.now() - time_filter
        ).select_related(
            'device__location'
        )
        
        # Фильтр по локации (если указана)
        if location_id:
            queryset = queryset.filter(device__location_id=location_id)
        
        # Группировка данных
        grouped_data = queryset.annotate(
            time_period=trunc_function('recorded_at'),
            location_id=F('device__location__id'),
            location_name=F('device__location__location_name'),
            date=F('recorded_at__date')
        ).values(
            'location_id', 
            'location_name',
            'time_period',
            'date'
        ).annotate(
            avg_temperature=Avg('temperature'),
            min_temperature=Min('temperature'),
            max_temperature=Max('temperature'),
            avg_humidity=Avg('humidity'),
            max_co2=Max('co2_level'),
            avg_co2=Avg('co2_level'),
            hazard_index=Avg('analyzedinformation__fire_hazard'),
            device_count=Count('device', distinct=True)
        ).order_by(
            'location_name', 
            'time_period'
        )
        
        # Сериализация и возврат результата
        serializer = TimeLocationGroupedSerializer(grouped_data, many=True)
        return Response({
            'time_range': time_range,
            'days': days if days > 0 else None,
            'location_filter': location_id,
            'results': serializer.data
        })