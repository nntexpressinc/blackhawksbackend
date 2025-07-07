from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.load.models.csv_import import GoogleSheetsImport
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=GoogleSheetsImport)
def process_import_automatically(sender, instance, created, **kwargs):
    """Import yaratilgandan so'ng avtomatik ishga tushirish"""
    if created and not instance.is_processed:
        try:
            logger.info(f"Avtomatik import boshlandi: {instance.id}")
            instance.process_excel()
            logger.info(f"Avtomatik import tugadi: {instance.id}")
        except Exception as e:
            logger.error(f"Avtomatik import xatoligi: {str(e)}")