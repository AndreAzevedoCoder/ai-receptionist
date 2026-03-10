from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tenant
from .serializers import TenantPublicSerializer, TenantUpdateSerializer


class TenantMeView(APIView):
    """
    Get current user's tenant information.

    GET /api/tenants/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tenant = request.user.tenant
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TenantPublicSerializer(tenant)
        return Response(serializer.data)

    def patch(self, request):
        """Update tenant information."""
        try:
            tenant = request.user.tenant
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TenantUpdateSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(TenantPublicSerializer(tenant).data)


class TenantStatusView(APIView):
    """
    Get tenant status.

    GET /api/tenants/me/status/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            tenant = request.user.tenant
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response({
            'status': tenant.status,
            'is_active': tenant.is_active,
            'agent_count': tenant.agent_count,
        })
