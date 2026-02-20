from django.apps import AppConfig
import MyApp.signals


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'MyApp'

    def ready(self):
        import MyApp.signals