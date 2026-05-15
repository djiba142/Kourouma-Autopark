from django.apps import AppConfig


class ProduitsConfig(AppConfig):
    name = 'produits'

    def ready(self):
        import produits.signals
