from django.urls import path
from .views import DashboardHomeView, DeviceMapView

app_name = "dashboard"          # позволяет писать {% url "dashboard:home" %}

urlpatterns = [
    path("",      DashboardHomeView.as_view(), name="home"),       # /dashboard/
    path("map/",  DeviceMapView.as_view(),   name="device-map"),   # /dashboard/map/
]