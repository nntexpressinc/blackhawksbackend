from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'
    label = 'apps_chat'

    def ready(self):
        import apps.chat.signals
