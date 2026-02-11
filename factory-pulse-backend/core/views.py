from datetime import timedelta

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from celery.result import AsyncResult

from .tasks import sum_sanity_check, generate_oee_report
from .models import Machine, ProductionEvent, SensorReading
from .serializers import (
    MachineSerializer,
    MachineDetailSerializer,
    SensorReadingSerializer,
    UserSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    API Endpoint for User Registration.
    Allows unauthenticated users to create a new account.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
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
    Calculates OEE metrics (Availability, Performance, Quality)
    based on the last 24 hours of telemetry data.
    """

    def get(self, request, device_id):
        machine = get_object_or_404(Machine, device_id=device_id)

        # Rolling window: last 24 hours
        now = timezone.now()
        start_time = now - timedelta(hours=24)

        events = machine.events.filter(timestamp__gte=start_time)
        readings = machine.readings.filter(
            timestamp__gte=start_time
        ).order_by('timestamp')

        # -----------------------------
        # 1. AVAILABILITY
        # -----------------------------
        total_seconds = (now - start_time).total_seconds()

        # MVP downtime logic:
        # Each ERROR_START represents ~5 minutes of downtime
        error_starts = events.filter(event_type='ERROR_START')
        downtime_seconds = error_starts.count() * 300

        run_time = max(0, total_seconds - downtime_seconds)
        availability = (
            (run_time / total_seconds) * 100
            if total_seconds > 0 else 0
        )

        # -----------------------------
        # 2. PERFORMANCE
        # -----------------------------
        total_produced = events.filter(event_type='CYCLE').count()

        if run_time > 0 and machine.ideal_cycle_time > 0:
            theoretical_max = run_time / machine.ideal_cycle_time
            performance = (
                (total_produced / theoretical_max) * 100
                if theoretical_max > 0 else 0
            )
        else:
            performance = 0

        # -----------------------------
        # 3. QUALITY
        # -----------------------------
        total_scraps = events.filter(event_type='SCRAP').count()
        good_parts = max(0, total_produced - total_scraps)

        quality = (
            (good_parts / total_produced) * 100
            if total_produced > 0 else 100
        )

        # -----------------------------
        # GLOBAL OEE
        # -----------------------------
        oee_score = (availability * performance * quality) / 10000

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
                "global": round(oee_score, 1),
            },
            # Last 50 points only (payload optimization)
            "energy_history": SensorReadingSerializer(
                readings.reverse()[:50][::-1],
                many=True
            ).data,
        }

        return Response(data)

@api_view(['POST'])
@permission_classes([AllowAny])
def trigger_task_view(request):
    """
    Triggers an asynchronous task
    """
    task_type = request.data.get('type', 'sum')

    if task_type == 'sum':
        task = sum_sanity_check.delay(10, 20)
    else:
        machine_id = request.data.get('machine_id', 1)
        task = generate_oee_report.delay(machine_id)

    return Response(
        {
            "message": "Task queued successfully!",
            "task_id": task.id,
        },
        status=202
    )

@api_view(['GET'])
@permission_classes([AllowAny])
def check_task_status_view(request, task_id):
    """
    Checks the status of a task
    """
    task_result = AsyncResult(task_id)

    return Response({
        "task_id": task_id,
        "status": task_result.status,
        "result": task_result.result if task_result.ready() else None,
    })