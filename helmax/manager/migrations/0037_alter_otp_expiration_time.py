# Generated by Django 5.1.4 on 2025-01-27 02:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0036_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 1, 27, 2, 46, 56, 572508, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
