# monitoring/filters.py
import django_filters
from .models import Device, Alarm, Location


class DeviceFilter(django_filters.FilterSet):
    """
    Расширенный фильтр устройств.
    ?location=<id>         – только устройства из локации
    ?alarm_level=critical  – только устройства, у которых есть активная тревога нужного уровня
    ?has_coords=1          – только устройства с заполненными координатами
    """

    location = django_filters.ModelChoiceFilter(queryset=Location.objects.all())
    alarm_level = django_filters.CharFilter(method="filter_alarm_level")
    has_coords = django_filters.BooleanFilter(method="filter_has_coords")

    class Meta:
        model = Device
        fields = ["location", "alarm_level", "has_coords"]

    def filter_alarm_level(self, qs, name, value):
        if not value:
            return qs
        return qs.filter(
            alarms__alarm_level=value,
            alarms__status="active",
        ).distinct()

    def filter_has_coords(self, qs, name, value):
        if value:
            return qs.filter(latitude__isnull=False, longitude__isnull=False)
        return qs