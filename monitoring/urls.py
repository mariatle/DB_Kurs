from django.urls import path, include
from rest_framework import routers
from .views import (
    LocationViewSet,
    DeviceViewSet,
    EnvironmentalParametersViewSet,
    AnalyzedInformationViewSet,
    IncidentViewSet,
    AlarmViewSet,
    TimeLocationGroupedView
)

router = routers.DefaultRouter()
router.register(r'locations', LocationViewSet)
router.register(r'devices', DeviceViewSet)
router.register(r'environmental-parameters', EnvironmentalParametersViewSet)
router.register(r'analyzed-information', AnalyzedInformationViewSet)
router.register(r'incidents', IncidentViewSet)
router.register(r'alarms', AlarmViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('time-location-stats/', TimeLocationGroupedView.as_view(), name='time-location-stats'),
]