# Generated by Django 5.2 on 2025-07-04 15:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps_load', '0040_driverpay_cd_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='driverpay',
            name='company_driver_data',
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
        migrations.AddField(
            model_name='driverpay',
            name='company_driver_pay',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='driverpay',
            name='miles_rate',
            field=models.FloatField(blank=True, default=0.65, null=True),
        ),
        migrations.AddField(
            model_name='driverpay',
            name='total_miles',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
