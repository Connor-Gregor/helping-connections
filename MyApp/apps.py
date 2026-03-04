from django.apps import AppConfig

class MyAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "MyApp"

    def ready(self):
        # Import signals only when apps are ready
        import MyApp.signals