# Generated by Django 5.1.7 on 2025-04-11 16:43

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0005_incident_location_incident_time_window_end_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incident',
            name='time_window_start',
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name='Начало временного окна'),
        ),
    ]
