# Generated by Django 5.1.1 on 2025-01-06 13:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="material",
        ),
        migrations.RemoveField(
            model_name="product",
            name="vehicle_service_type",
        ),
    ]
