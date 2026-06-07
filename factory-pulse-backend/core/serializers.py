from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import serializers

from .analytics import calculate_oee
from .models import Machine, SensorReading


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
    Computes a live rolling-24h OEE snapshot for the card view, the same
    calculation MachineDetailView and the AI layer use.
    """
    oee = serializers.SerializerMethodField()

    class Meta:
        model = Machine
        fields = [
            'id', 'name', 'device_id', 'machine_type',
            'description', 'image', 'ideal_cycle_time', 'oee'
        ]

    def get_oee(self, machine):
        now = timezone.now()
        return calculate_oee(machine, now - timedelta(hours=24), now)


class MachineDetailSerializer(serializers.ModelSerializer):
    """
    Detailed Serializer for the Machine Dashboard view.
    Includes full historical telemetry data ('energy_history') for charting.
    """
    oee = serializers.SerializerMethodField()

    # Maps the 'readings' related_name from the Model to 'energy_history' in the JSON response
    energy_history = SensorReadingSerializer(many=True, read_only=True, source='readings')

    class Meta:
        model = Machine
        fields = [
            'id', 'name', 'device_id', 'machine_type',
            'description', 'image', 'oee', 'energy_history'
        ]

    def get_oee(self, machine):
        now = timezone.now()
        return calculate_oee(machine, now - timedelta(hours=24), now)


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