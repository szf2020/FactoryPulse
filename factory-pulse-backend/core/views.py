from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.permissions import AllowAny

# Local Imports
from .models import Machine, ProductionEvent, SensorReading
from .serializers import (
    MachineSerializer, 
    MachineDetailSerializer, 
    SensorReadingSerializer, 
    UserSerializer
)

class RegisterView(generics.CreateAPIView):
    """
    API Endpoint for User Registration.
    Allows unauthenticated users to create a new account.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,) # Open access for registration
    serializer_class = UserSerializer


class MachineListView(APIView):
    """
    API Endpoint to list all registered machines.
    Returns a summary of each machine, including its current OEE snapshot.
    """
    def get(self, request):
        machines = Machine.objects.all()
        serializer = MachineSerializer(machines, many=True)
        return Response(serializer.data)


class MachineDetailView(APIView):
    """
    API Endpoint for detailed machine analytics.
    Calculates OEE metrics (Availability, Performance, Quality) on-the-fly
    based on the last 24 hours of telemetry data.
    """
    def get(self, request, device_id):
        machine = get_object_or_404(Machine, device_id=device_id)
        
        # Filter data for the last 24 hours (Rolling Window)
        now = timezone.now()
        start_time = now - timedelta(hours=24)
        
        events = machine.events.filter(timestamp__gte=start_time)
        readings = machine.readings.filter(timestamp__gte=start_time).order_by('timestamp')

        # --- 1. AVAILABILITY CALCULATION ---
        # Formula: Run Time / Total Time
        total_seconds = (now - start_time).total_seconds()
        
        # Calculate Downtime
        # MVP Logic: We count 'ERROR_START' events and assume a fixed average downtime 
        # of 5 minutes (300s) per stop for estimation purposes.
        # Future Improvement: Calculate exact delta between ERROR_START and ERROR_END timestamps.
        error_starts = events.filter(event_type='ERROR_START')
        downtime_seconds = error_starts.count() * 300 
        
        run_time = max(0, total_seconds - downtime_seconds)
        availability = (run_time / total_seconds) * 100 if total_seconds > 0 else 0

        # --- 2. PERFORMANCE CALCULATION ---
        # Formula: Total Produced / (Run Time / Ideal Cycle Time)
        total_produced = events.filter(event_type='CYCLE').count()
        
        if run_time > 0 and machine.ideal_cycle_time > 0:
            theoretical_max = run_time / machine.ideal_cycle_time
            performance = (total_produced / theoretical_max) * 100 if theoretical_max > 0 else 0
        else:
            performance = 0

        # --- 3. QUALITY CALCULATION ---
        # Formula: Good Parts / Total Parts
        # Logic: Our firmware sends 'CYCLE' for every part, and 'SCRAP' for bad parts.
        # Therefore: Good Parts = Total Cycles - Scrap Count
        total_scraps = events.filter(event_type='SCRAP').count()
        good_parts = max(0, total_produced - total_scraps)
        
        # If nothing was produced, Quality is theoretically 100% (no defects generated)
        quality = (good_parts / total_produced) * 100 if total_produced > 0 else 100

        # --- GLOBAL OEE SCORE ---
        # Standard Industry Formula: (A * P * Q)
        oee_score = (availability * performance * quality) / 10000 # Divided by 100^2 to normalize percentages

        # Construct the JSON Response
        data = {
            "id": machine.id,
            "name": machine.name,
            "device_id": machine.device_id,
            "machine_type": machine.machine_type,
            "description": machine.description,
            "image": machine.image.url if machine.image else None,
            "oee": {
                "availability": round(availability, 1),
                "performance": round(performance, 1),
                "quality": round(quality, 1),
                "global": round(oee_score, 1)
            },
            # Chart Data: Return only the last 50 data points to optimize payload size
            "energy_history": SensorReadingSerializer(readings.reverse()[:50][::-1], many=True).data
        }

        return Response(data)