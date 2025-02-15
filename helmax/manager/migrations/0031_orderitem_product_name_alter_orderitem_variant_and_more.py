# Generated by Django 5.1.4 on 2025-01-27 01:23

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("manager", "0030_order_billing_address_order_delivery_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="product_name",
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name="orderitem",
            name="variant",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="manager.variant",
            ),
        ),
        migrations.AlterField(
            model_name="otp",
            name="expiration_time",
            field=models.DateTimeField(
                default=datetime.datetime(
                    2025, 1, 27, 1, 24, 29, 422014, tzinfo=datetime.timezone.utc
                )
            ),
        ),
    ]
