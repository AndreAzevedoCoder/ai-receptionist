from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Lead
from .serializers import LeadSerializer


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leads.

    Provides list, create, retrieve, update, and delete operations.
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Lead.objects.all()

        # Filter by phone number
        phone_number = self.request.query_params.get('phone_number')
        if phone_number:
            queryset = queryset.filter(phone_number=phone_number)

        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)

        return queryset
