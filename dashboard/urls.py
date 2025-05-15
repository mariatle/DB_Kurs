# dashboard/urls.py
from django.urls import path

from monitoring.views import hazard_series
from . import views

app_name = "dashboard"

urlpatterns = [
    path("",  views.DashboardHomeView.as_view(), name="home"),
    path("map/", views.DeviceMapView.as_view(), name="device-map"),
    path("device/<int:device_id>/hazard-series/", hazard_series,
         name="device-hazard-series"),
]