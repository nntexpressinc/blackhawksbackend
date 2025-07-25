# Generated by Django 5.2 on 2025-07-04 19:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps_load', '0043_delete_amazonrelaypayment'),
    ]

    operations = [
        migrations.CreateModel(
            name='AmazonRelayPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(upload_to='amazon_relay_files/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed')], default='pending', max_length=20)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('loads_updated', models.IntegerField(default=0)),
                ('error_message', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Amazon Relay Payment',
                'verbose_name_plural': 'Amazon Relay Payments',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='AmazonRelayProcessedRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trip_id', models.CharField(blank=True, max_length=100, null=True)),
                ('load_id', models.CharField(blank=True, max_length=100, null=True)),
                ('route', models.CharField(blank=True, max_length=200)),
                ('gross_pay', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('start_date', models.DateField(blank=True, null=True)),
                ('end_date', models.DateField(blank=True, null=True)),
                ('distance', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('is_matched', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('matched_load', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='apps_load.load')),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='processed_records', to='apps_load.amazonrelaypayment')),
            ],
            options={
                'verbose_name': 'Amazon Relay Processed Record',
                'verbose_name_plural': 'Amazon Relay Processed Records',
            },
        ),
    ]
