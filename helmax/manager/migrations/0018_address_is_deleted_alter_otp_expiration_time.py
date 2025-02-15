# Generated by Django 5.1.4 on 2025-01-24 21:56

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0017_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AddField(
            model_name="address",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 1, 24, 21, 57, 47, 782091, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
