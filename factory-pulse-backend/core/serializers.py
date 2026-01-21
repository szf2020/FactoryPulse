from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Machine, SensorReading, OeeData

class OeeSerializer(serializers.ModelSerializer):
    """
    Serializes OEE (Overall Equipment Effectiveness) metrics.
    Used as a nested object within Machine serializers.
    """
    class Meta:
        model = OeeData
        fields = ['availability', 'performance', 'quality']


class SensorReadingSerializer(serializers.ModelSerializer):
    """
    Serializes high-frequency telemetry data (Time-Series).
    Used for generating charts on the frontend.
    """
    current_amps = serializers.FloatField()
    
    class Meta:
        model = SensorReading
        fields = ['timestamp', 'current_amps']


class MachineSerializer(serializers.ModelSerializer):
    """
    Standard Serializer for the Machine List view.
    Includes a snapshot of current OEE data for the card view.
    """
    oee = OeeSerializer(read_only=True) 

    class Meta:
        model = Machine
        fields = [
            'id', 'name', 'device_id', 'machine_type', 
            'description', 'image', 'ideal_cycle_time', 'oee'
        ]


class MachineDetailSerializer(serializers.ModelSerializer):
    """
    Detailed Serializer for the Machine Dashboard view.
    Includes full historical telemetry data ('energy_history') for charting.
    """
    oee = OeeSerializer(read_only=True)
    
    # Maps the 'readings' related_name from the Model to 'energy_history' in the JSON response
    energy_history = SensorReadingSerializer(many=True, read_only=True, source='readings')

    class Meta:
        model = Machine
        fields = [
            'id', 'name', 'device_id', 'machine_type', 
            'description', 'image', 'oee', 'energy_history'
        ]


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User Registration.
    Handles secure password hashing during creation.
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user