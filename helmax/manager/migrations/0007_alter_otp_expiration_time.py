# Generated by Django 5.1.1 on 2025-01-07 06:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0006_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 1, 7, 6, 33, 14, 191772, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
