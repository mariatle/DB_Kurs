# Generated by Django 5.1.7 on 2025-05-04 21:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0009_incident_location'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='environmentalparameters',
            name='wind_speed',
        ),
    ]
