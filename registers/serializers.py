from rest_framework import serializers
from .models import Register


class RegisterSerializer(serializers.ModelSerializer):
    """
    Full serializer for the Register model.
    Includes denormalized fields for easier consumption.
    """

    tracker_name  = serializers.CharField(source='tracker.name', read_only=True)
    tracker_type  = serializers.CharField(source='tracker.type', read_only=True)
    vehicle_name  = serializers.CharField(source='tracker.vehicle.name', read_only=True)
    vehicle_id    = serializers.IntegerField(source='tracker.vehicle.id', read_only=True)

    class Meta:
        model = Register
        fields = [
            'id',
            'tracker',
            'tracker_name',
            'tracker_type',
            'vehicle_id',
            'vehicle_name',
            'kilometers',
            'amount',
            'tracker_at',
            'note',
            'active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_kilometers(self, value: int) -> int:
        """
        Ensure the km registered is not lower than the tracker's last service km.
        """
        tracker = self.initial_data.get('tracker')
        if tracker:
            from trackers.models import Tracker
            try:
                t = Tracker.objects.get(pk=tracker)
                if value < t.last_service_km:
                    raise serializers.ValidationError(
                        'kilometers cannot be less than the tracker\'s last_service_km.'
                    )
            except Tracker.DoesNotExist:
                pass
        return value


class RegisterListSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for listing registers efficiently.
    """

    tracker_name = serializers.CharField(source='tracker.name', read_only=True)
    tracker_type = serializers.CharField(source='tracker.type', read_only=True)

    class Meta:
        model = Register
        fields = [
            'id',
            'tracker',
            'tracker_name',
            'tracker_type',
            'kilometers',
            'amount',
            'tracker_at',
            'active',
        ]
