from rest_framework import permissions

class IsBSGAdmin(permissions.BasePermission):
    """
    Permission permettant uniquement aux administrateurs BSG d'accéder à la ressource.
    Vérifie le champ 'role' du modèle Utilisateur.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'ADMIN')

class IsBSGEmploye(permissions.BasePermission):
    """
    Permission permettant aux employés BSG d'accéder à la ressource.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'EMPLOYE')

class IsBSGMagasinier(permissions.BasePermission):
    """
    Permission permettant uniquement aux magasiniers BSG d'accéder à la ressource.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'MAGASINIER')

class IsBSGAdminOrMagasinier(permissions.BasePermission):
    """
    Permission pour Admin OU Magasinier (stock, achats).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in ('ADMIN', 'MAGASINIER')
        )

class IsBSGAdminOrEmploye(permissions.BasePermission):
    """
    Permission pour Admin OU Employé (commandes, clients).
    """
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and request.user.role in ('ADMIN', 'EMPLOYE')
        )
