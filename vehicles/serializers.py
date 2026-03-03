from rest_framework import serializers
from .models import Vehicle

class VehicleSerializer(serializers.ModelSerializer):
    """
    Serializer for the Vehicle model.
    """
    
    owner_username = serializers.CharField(source='user.username', read_only=True)
    trackers_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = [
            'id',
            'user',
            'brand',
            'model',
            'year',
            'name',
            'kilometers',
            'created_at',
            'updated_at',
            'is_active',
            'owner_username',
            'trackers_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_trackers_count(self, obj: Vehicle) -> int:
        """
        Get the count of active trackers associated with the vehicle.
        """
        return getattr(obj, 'trackers').filter(active=True).count()
    
    def validate_year(self, value: int) -> int:
        """
        Validate that the year is within a reasonable range.
        """
        import datetime
        current_year = datetime.datetime.now().year
        if value < 1900 or value > (current_year + 5):  # The first car was invented around 1886
            raise serializers.ValidationError("Please enter a valid year for the vehicle.")
        return value
    
class VehicleListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing vehicles with minimal details.

    Args:
        serializers (ModelSerializer): Base serializer class.
    """
    
    class Meta:
        model = Vehicle
        fields = ['id', 'brand', 'model', 'year', 'name', 'kilometers']