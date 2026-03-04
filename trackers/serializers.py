from rest_framework import serializers
from .models import Tracker


class TrackerSerializer(serializers.ModelSerializer):
    """
    Serializer for the Tracker model.
    """

    vehicle_name    = serializers.CharField(source='vehicle.name', read_only=True)
    is_due          = serializers.SerializerMethodField()
    registers_count = serializers.SerializerMethodField()

    class Meta:
        model = Tracker
        fields = [
            'id',
            'vehicle',
            'vehicle_name',
            'type',
            'name',
            'icon',
            'unit',
            'interval_value',
            'last_service_km',
            'last_service_at',
            'next_due_km',
            'next_due_at',
            'is_active',
            'created_at',
            'updated_at',
            'is_due',
            'registers_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_due(self, obj: Tracker) -> bool:
        """
        Returns True if the tracker is overdue based on current vehicle kilometers.
        """
        vehicle_km = obj.vehicle.kilometers
        if obj.next_due_km and vehicle_km >= obj.next_due_km:
            return True
        return False

    def get_registers_count(self, obj: Tracker) -> int:
        """
        Returns the total number of active service registers for this tracker.
        """
        return obj.registers.filter(is_active=True).count()

    def validate(self, attrs):
        """
        Ensure next_due_km is greater than last_service_km when both are provided.
        """
        last_km = attrs.get('last_service_km', getattr(self.instance, 'last_service_km', 0))
        next_km = attrs.get('next_due_km', getattr(self.instance, 'next_due_km', 0))

        if next_km and next_km <= last_km:
            raise serializers.ValidationError(
                {'next_due_km': 'next_due_km must be greater than last_service_km.'}
            )
        return attrs


class TrackerListSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for listing trackers.
    """

    is_due = serializers.SerializerMethodField()

    class Meta:
        model = Tracker
        fields = ['id', 'vehicle', 'type', 'name', 'icon', 'unit', 'next_due_km', 'is_active', 'is_due']

    def get_is_due(self, obj: Tracker) -> bool:
        vehicle_km = obj.vehicle.kilometers
        if obj.next_due_km and vehicle_km >= obj.next_due_km:
            return True
        return False
