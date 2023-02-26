from django.apps import AppConfig


class RegistrarportalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'registrarportal'

    def ready(self):
        import registrarportal.signals
