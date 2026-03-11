from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Lead, LeadAnswer
from .serializers import LeadSerializer, LeadListSerializer, LeadAnswerSerializer


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing leads.

    Provides list, create, retrieve, update, and delete operations.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return LeadListSerializer
        return LeadSerializer

    def get_queryset(self):
        # Get user's tenant
        try:
            tenant = self.request.user.tenant
        except Exception:
            return Lead.objects.none()

        queryset = Lead.objects.filter(tenant=tenant).prefetch_related('answers')

        # Search by name, phone, or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone_number__icontains=search) |
                Q(email__icontains=search)
            )

        # Filter by source
        source = self.request.query_params.get('source')
        if source:
            queryset = queryset.filter(source=source)

        return queryset

    def perform_create(self, serializer):
        # Set tenant when creating a lead
        try:
            tenant = self.request.user.tenant
            serializer.save(tenant=tenant)
        except Exception:
            serializer.save()

    @action(detail=True, methods=['post'])
    def answers(self, request, pk=None):
        """Add a new answer to a lead."""
        lead = self.get_object()
        serializer = LeadAnswerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(lead=lead, source='manual')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LeadAnswerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing lead answers.

    Allows CRUD operations on answers.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LeadAnswerSerializer

    def get_queryset(self):
        try:
            tenant = self.request.user.tenant
        except Exception:
            return LeadAnswer.objects.none()

        return LeadAnswer.objects.filter(lead__tenant=tenant)

    def perform_create(self, serializer):
        # Set source to manual when created via API
        serializer.save(source='manual')

    def perform_update(self, serializer):
        # Keep original source or set to manual if not provided
        if 'source' not in serializer.validated_data:
            serializer.save(source='manual')
        else:
            serializer.save()
