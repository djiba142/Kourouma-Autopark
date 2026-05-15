from rest_framework import generics, permissions
from .models import LogActivite
from .serializers import LogActiviteSerializer

class AuditListView(generics.ListAPIView):
    queryset = LogActivite.objects.all()
    serializer_class = LogActiviteSerializer
    permission_classes = [permissions.IsAdminUser]
