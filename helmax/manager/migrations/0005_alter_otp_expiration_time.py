# Generated by Django 5.1.1 on 2025-01-07 04:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0004_review"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 1, 7, 4, 58, 8, 872513, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
