from django.apps import AppConfig


class LoadConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.load'
    label = 'apps_load'

    def ready(self):
        import apps.load.signals
        import apps.load.models.amazon
        import apps.load.csv_signals