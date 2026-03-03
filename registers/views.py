from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Register
from .serializers import RegisterSerializer, RegisterListSerializer


class RegisterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for maintenance registers.

    A register records when a service was performed for a tracker
    (e.g. oil change, tire rotation, part replacement).

    On creation, the related tracker is automatically updated:
      - last_service_km  ← register.kilometers
      - next_due_km      ← register.kilometers + tracker.interval_value
      - last_service_at  ← register.tracker_at

    Only registers belonging to the authenticated user's vehicles are exposed.
    Staff users can see all registers.
    """

    queryset = Register.objects.all()
    serializer_class = RegisterSerializer

    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tracker', 'tracker__vehicle', 'active']
    search_fields    = ['note', 'tracker__name', 'tracker__type']
    ordering_fields  = ['tracker_at', 'kilometers', 'amount', 'created_at']
    ordering         = ['-tracker_at']

    def get_queryset(self):
        """
        Scope queryset to the authenticated user's vehicles.
        Staff users can access all registers.
        """
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'tracker',
            'tracker__vehicle',
            'tracker__vehicle__user',
        )

        if not self.request.user.is_staff:
            queryset = queryset.filter(tracker__vehicle__user=self.request.user)

        if self.action == 'list':
            queryset = queryset.filter(active=True)

        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return RegisterListSerializer
        return RegisterSerializer

    def perform_create(self, serializer):
        """
        Save the register and sync the tracker's service state automatically.
        """
        register = serializer.save()
        self._sync_tracker(register)

    def perform_update(self, serializer):
        """
        Save the register and re-sync the tracker if kilometers changed.
        """
        register = serializer.save()
        self._sync_tracker(register)

    def _sync_tracker(self, register: Register) -> None:
        """
        Update the tracker after a register is saved.
        Sets last_service_km, next_due_km and last_service_at based on the
        most recent active register for that tracker.
        """
        tracker = register.tracker

        # Use the most recent active register to determine the latest service state
        latest = (
            Register.objects
            .filter(tracker=tracker, active=True)
            .order_by('-kilometers')
            .first()
        )

        if latest:
            tracker.last_service_km = latest.kilometers
            tracker.next_due_km     = latest.kilometers + tracker.interval_value
            tracker.last_service_at = latest.tracker_at

        tracker.save(update_fields=['last_service_km', 'next_due_km', 'last_service_at'])
