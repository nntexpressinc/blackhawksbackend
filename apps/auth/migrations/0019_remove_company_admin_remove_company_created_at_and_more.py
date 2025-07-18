# Generated by Django 5.2 on 2025-07-03 16:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps_auth', '0018_user_company_user_profile_photo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='admin',
        ),
        migrations.RemoveField(
            model_name='company',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='company',
            name='name',
        ),
        migrations.RemoveField(
            model_name='company',
            name='updated_at',
        ),
        migrations.AddField(
            model_name='company',
            name='city',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='company_logo',
            field=models.FileField(blank=True, null=True, upload_to='company-logo'),
        ),
        migrations.AddField(
            model_name='company',
            name='company_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='fax',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='phone',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='state',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='zip',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
