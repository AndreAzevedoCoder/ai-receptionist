import logging

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """
    Register a new user and create a tenant.

    POST /api/auth/register/
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user, tenant = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        logger.info(f"New user registered: {user.email}, tenant: {tenant.id}")

        # Trigger provisioning (will be implemented in provisioning service)
        # For now, just mark as pending
        # provision_tenant.delay(tenant.id)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Registration successful. Your phone number is being provisioned.',
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """
    Get current user information.

    GET /api/auth/me/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        """Update user profile."""
        user = request.user
        allowed_fields = ['first_name', 'last_name']

        for field in allowed_fields:
            if field in request.data:
                setattr(user, field, request.data[field])

        user.save()
        return Response(UserSerializer(user).data)
