from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Tracker
from .serializers import TrackerSerializer, TrackerListSerializer


class TrackerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing trackers.

    Provides CRUD operations for vehicle trackers.
    Supports filtering by vehicle, type, and active status.
    Only returns trackers belonging to the current user's vehicles.
    """

    queryset = Tracker.objects.all()
    serializer_class = TrackerSerializer

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehicle', 'type', 'active']
    search_fields    = ['name', 'type']
    ordering_fields  = ['created_at', 'next_due_km', 'last_service_km']
    ordering         = ['-created_at']

    def get_queryset(self):
        """
        Restrict trackers to those belonging to the current user's vehicles.
        Staff users can see all trackers.
        """
        queryset = super().get_queryset()
        queryset = queryset.select_related('vehicle', 'vehicle__user')

        if not self.request.user.is_staff:
            queryset = queryset.filter(vehicle__user=self.request.user)

        if self.action == 'list':
            queryset = queryset.filter(active=True)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return TrackerListSerializer
        return TrackerSerializer

    @action(detail=True, methods=['post'])
    def record_service(self, request, pk=None):
        """
        Record a service event for this tracker.
        Updates last_service_km, last_service_at, and recalculates next_due values.

        Expected body:
            {
                "service_km": 45000,
                "service_at": "2026-02-23T10:00:00Z"  (optional)
            }
        """
        tracker = self.get_object()
        service_km = request.data.get('service_km')
        service_at = request.data.get('service_at')

        if service_km is None:
            return Response(
                {'error': 'service_km is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            service_km = int(service_km)
        except (ValueError, TypeError):
            return Response(
                {'error': 'service_km must be a valid integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if service_km < tracker.last_service_km:
            return Response(
                {'error': 'service_km cannot be less than the previous last_service_km.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tracker.last_service_km = service_km
        tracker.next_due_km = service_km + tracker.interval_value

        if service_at:
            tracker.last_service_at = service_at

        tracker.save()

        serializer = TrackerSerializer(tracker)
        return Response(serializer.data)
