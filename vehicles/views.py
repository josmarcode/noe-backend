from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Vehicle
from .serializers import VehicleSerializer, VehicleListSerializer

class VehicleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing vehicles.

    Provides CRUD operations and additional actions for vehicles.
    """
    
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    
    # Filtering and searching
    filter_backends     = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields    = ['brand', 'year', 'active', 'user']
    search_fields       = ['brand', 'model', 'name']
    ordering_fields     = ['created_at', 'year', 'kilometers']
    ordering            = ['-created_at']
    
    def get_queryset(self):
        """
        Custom queryset to optimize queries
        """
        
        queryset = super().get_queryset()
        
        # Optimze makeing a unique query
        queryset = queryset.select_related('user')
        queryset = queryset.prefetch_related('trackers')
        
        # Filter for user (only return user vehicles)
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
            
        # Only return active vehicles by default
        if self.action == 'list':
            queryset = queryset.filter(active=True)
            
        return queryset
    
    def get_serializer_class(self) -> type[VehicleListSerializer] | type[VehicleSerializer]:  # type: ignore[override]
        """
        Use a different serializer for list action to optimize performance.
        """
        
        if self.action == 'list':
            return VehicleListSerializer
        return VehicleSerializer
    
    def perform_create(self, serializer):
        """
        Custom create method to assign the current user as the owner of the vehicle.
        
        Args:
            serializer (VehicleSerializer): The serializer instance with validated data.
        """
        
        serializer.save(user=self.request.user)
        
    @action(detail=True, methods=['post'])
    def update_kilometers(self, request, pk=None):
        """
        Custom action to update the kilometers of a vehicle.

        Args:
            request (Request): The incoming request containing the new kilometers value.
            pk (str): The primary key of the vehicle to update.

        Returns:
            Response: A response indicating success or failure of the update operation.
        """
        
        vehicle = self.get_object()
        new_km = request.data.get('kilometers')
        
        if not new_km:
            return Response(
                {
                    'error': 'Kilometers value is required.'
                }, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_km = int(new_km)
            if new_km < vehicle.kilometers:
                return Response(
                    {
                        'error': 'New kilometers value cannot be less than the current value.'
                    }, status=status.HTTP_400_BAD_REQUEST
                )
            
            vehicle.kilometers = new_km
            vehicle.save()
            
            serializer = self.get_serializer(vehicle)
            return Response(serializer.data)
        
        except ValueError:
            return Response(
                {
                    'error': 'Invalid kilometers value. Please provide a valid integer.'
                }, status=status.HTTP_400_BAD_REQUEST
            )
