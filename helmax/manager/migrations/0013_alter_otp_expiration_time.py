# Generated by Django 5.1.4 on 2025-01-20 09:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0012_remove_category_is_deleted_alter_otp_expiration_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 1, 20, 9, 42, 13, 834096, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
