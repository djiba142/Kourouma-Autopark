from django.apps import AppConfig


class WebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'web'

    def ready(self):
        import web.views_notifications   # enregistre les signals stock
        import web.views_securite        # enregistre les signals auth
