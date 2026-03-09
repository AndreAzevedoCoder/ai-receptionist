from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import CallLog
from .serializers import CallLogSerializer


class CallLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing call logs.

    Read-only - call logs are created by Twilio webhooks.
    """
    queryset = CallLog.objects.all()
    serializer_class = CallLogSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = CallLog.objects.select_related('lead').all()

        # Filter by phone number
        from_number = self.request.query_params.get('from_number')
        if from_number:
            queryset = queryset.filter(from_number=from_number)

        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset
