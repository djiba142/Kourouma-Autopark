from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from auth_users.models import Utilisateur

class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(Utilisateur.USERNAME_FIELD)
        
        try:
            # Recherche par email ou par téléphone
            user = Utilisateur.objects.get(Q(email=username) | Q(telephone=username))
            if user.check_password(password):
                return user
        except Utilisateur.DoesNotExist:
            return None
        except Exception:
            return None
