from datetime import timedelta

from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from celery.result import AsyncResult

from .analytics import calculate_oee, resolve_period, summarize_downtime
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

        readings = machine.readings.filter(
            timestamp__gte=start_time
        ).order_by('timestamp')

        data = {
            "id": machine.id,
            "name": machine.name,
            "device_id": machine.device_id,
            "machine_type": machine.machine_type,
            "description": machine.description,
            "image": machine.image.url if machine.image else None,
            "oee": calculate_oee(machine, start_time, now),
            # Last 50 points only (payload optimization)
            "energy_history": SensorReadingSerializer(
                readings.reverse()[:50][::-1],
                many=True
            ).data,
        }

        return Response(data)


class MachineOeeView(APIView):
    """
    Read-only API Endpoint for OEE metrics of a single machine over a
    configurable period. Reuses the same calculation as MachineDetailView,
    parameterized by a 'period' query string (e.g. "30m", "24h", "7d").
    Defaults to "24h" when no period is provided.
    """

    def get(self, request, device_id):
        machine = get_object_or_404(Machine, device_id=device_id)
        period = request.query_params.get('period', '24h')
        start, end = resolve_period(period)

        return Response({
            "machine": machine.device_id,
            "name": machine.name,
            "period": period,
            "start": start,
            "end": end,
            "oee": calculate_oee(machine, start, end),
        })


class MachineDowntimeView(APIView):
    """
    Read-only API Endpoint listing stoppages for a single machine over a
    configurable period. Pairs ERROR_START/ERROR_END events into discrete
    intervals with measured durations (an open stoppage is reported as
    'ongoing'). Query param: 'period' (e.g. "30m", "24h", "7d"), default "24h".
    """

    def get(self, request, device_id):
        machine = get_object_or_404(Machine, device_id=device_id)
        period = request.query_params.get('period', '24h')
        start, end = resolve_period(period)

        return Response({
            "machine": machine.device_id,
            "name": machine.name,
            "period": period,
            "start": start,
            "end": end,
            **summarize_downtime(machine, start, end),
        })


class TopDowntimeView(APIView):
    """
    Read-only API Endpoint ranking machines by total downtime within a period.
    Query params: 'period' (default "24h") and 'limit' (default 5, max 50).
    """

    def get(self, request):
        period = request.query_params.get('period', '24h')
        start, end = resolve_period(period)

        try:
            limit = int(request.query_params.get('limit', 5))
        except ValueError:
            raise ValidationError("'limit' must be an integer.")
        limit = max(1, min(limit, 50))

        ranking = []
        for machine in Machine.objects.all():
            summary = summarize_downtime(machine, start, end)
            ranking.append({
                "machine": machine.device_id,
                "name": machine.name,
                "stoppage_count": summary["stoppage_count"],
                "total_downtime_seconds": summary["total_downtime_seconds"],
            })

        ranking.sort(key=lambda item: item["total_downtime_seconds"], reverse=True)

        return Response({
            "period": period,
            "start": start,
            "end": end,
            "ranking": ranking[:limit],
        })

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