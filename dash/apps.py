from django.apps import AppConfig


class DashConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dash'
    def ready(self):
        import dash.signals