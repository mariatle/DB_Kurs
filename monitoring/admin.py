from django.contrib import admin
from .models import *

admin.site.register(Location)
admin.site.register(Device)
admin.site.register(EnvironmentalParameters)
admin.site.register(AnalyzedInformation)
admin.site.register(Incident)
admin.site.register(Alarm)