from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import LoginView, MeView, RegisterEmployeView, LogoutView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
    path('employes/', RegisterEmployeView.as_view(), name='register_employe'),
    path('password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
]
