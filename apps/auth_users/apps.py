from django.apps import AppConfig


class AuthUsersConfig(AppConfig):
    name = 'auth_users'

    def ready(self):
        import auth_users.signals
