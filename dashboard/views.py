from datetime import timedelta
from django.utils import timezone
from django.db import models
from django.views.generic import TemplateView

from monitoring.models import Device, Alarm, Incident


class DashboardHomeView(TemplateView):
    """Главная панель с KPI и графиком тревог."""
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # KPI-счётчики
        ctx["device_total"]  = Device.objects.count()
        ctx["alarm_active"]  = Alarm.objects.filter(status="active").count()
        ctx["incident_open"] = Incident.objects.filter(
                                   status__in=["open", "investigation"]
                               ).count()

        # График &laquo;тревоги за 7 дней&raquo;
        today  = timezone.now().date()
        start  = today - timedelta(days=6)
        rows   = (Alarm.objects
                  .filter(alarm_at__date__gte=start)
                  .extra(select={"d": "DATE(alarm_at)"})
                  .values("d")
                  .order_by("d")
                  .annotate(cnt=models.Count("id")))
        ctx["chart_labels"] = [r["d"].strftime("%d.%m") for r in rows]
        ctx["chart_data"]   = [r["cnt"] for r in rows]

        # Последние критические тревоги
        ctx["latest_alarms"] = (
            Alarm.objects
            .filter(alarm_level__in=["high", "critical"])
            .select_related("analysis__recorded_data__device")
            .order_by("-alarm_at")[:10]
        )
        return ctx


class DeviceMapView(TemplateView):
    """Интерактивная карта устройств."""
    template_name = "dashboard/device_map.html"