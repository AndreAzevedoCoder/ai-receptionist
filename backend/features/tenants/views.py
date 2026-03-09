from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Tenant
from .serializers import TenantConfigSerializer, TenantPublicSerializer


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
        """Update tenant configuration."""
        try:
            tenant = request.user.tenant
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'No tenant associated with this account'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TenantConfigSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(TenantPublicSerializer(tenant).data)


class TenantStatusView(APIView):
    """
    Get tenant provisioning status.

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
            'is_provisioned': tenant.is_provisioned,
            'error': tenant.provisioning_error if tenant.status == 'failed' else None,
        })
