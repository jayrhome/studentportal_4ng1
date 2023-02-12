from django.apps import AppConfig


class UsersportalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usersPortal'

    def ready(self):
        import usersPortal.signals
