"""
web/middleware.py
─────────────────
AuditMiddleware  : enregistre chaque action POST dans le journal d'audit.
RoleGuard        : décorateurs pour protéger les vues par rôle.
"""
import logging
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# MIDDLEWARE — Audit automatique des actions POST
# ─────────────────────────────────────────────────────────────────────────────

class AuditMiddleware:
    """
    Enregistre toutes les requêtes POST (créations, modifications, actions)
    dans le journal d'audit Django. Lecture seule (GET) ignorée.
    """
    IGNORE_PATHS = ['/admin/', '/static/', '/media/', '/api/']

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (request.method == 'POST'
                and request.user.is_authenticated
                and not any(request.path.startswith(p) for p in self.IGNORE_PATHS)
                and response.status_code in (200, 201, 302)):
            try:
                from audit.models import AuditLog
                AuditLog.objects.create(
                    utilisateur=request.user,
                    action=f"{request.method} {request.path}",
                    details=str(request.POST.dict())[:500],
                    ip=self._get_ip(request),
                    date=timezone.now(),
                )
            except Exception as e:
                logger.warning("AuditMiddleware error: %s", e)

        return response

    def _get_ip(self, request):
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        return xff.split(',')[0] if xff else request.META.get('REMOTE_ADDR', '')


# ─────────────────────────────────────────────────────────────────────────────
# DÉCORATEURS DE RÔLE — à utiliser sur chaque vue
# ─────────────────────────────────────────────────────────────────────────────

def login_required_web(view_func):
    """Redirige vers /login/ si non connecté."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')
        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*roles):
    """
    Usage :
        @role_required('ADMIN')
        @role_required('ADMIN', 'EMPLOYE')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'/login/?next={request.path}')
            if request.user.role not in roles:
                messages.error(
                    request,
                    f"Accès refusé. Cette page est réservée aux : {', '.join(roles)}."
                )
                return redirect('web:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# Raccourcis fréquents
admin_required     = role_required('ADMIN')
employe_or_admin   = role_required('ADMIN', 'EMPLOYE')
magasinier_or_admin = role_required('ADMIN', 'MAGASINIER')
