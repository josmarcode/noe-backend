from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for custom user.
    """
    
    # Add a field to count the number of vehicles associated with the user
    vehicles_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'currency',
            'vehicles_count',
            'created_at',
            'updated_at',
        ]
        
        read_only_fields = ['id', 'created_at', 'updated_at', 'vehicles_count']
        
    def get_vehicles_count(self, obj):
        return obj.vehicles.filter(is_active=True).count()
    
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Args:
        serializers (ModelSerializer): Base serializer class.
    """
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [ 'username', 'email', 'password', 'first_name', 'last_name', 'currency' ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
        
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('This email is already registered.')
        return value
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for changing user password.

    Args:
        serializers (Serializer): Base serializer class.
    """
    
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password], style={'input_type': 'password'})