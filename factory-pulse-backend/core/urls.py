from django.urls import path
from .views import (
    MachineListView,
    MachineDetailView,
    MachineOeeView,
    MachineDowntimeView,
    TopDowntimeView,
)

urlpatterns = [
    # Endpoint to list all machines (Summary View)
    path('machines/', MachineListView.as_view(), name='machine-list'),

    # Read-only analytics endpoints (period-based), consumed by the dashboard
    # and by the AI layer (MCP server / assistant). Declared before the
    # generic detail route for readability, though the 'str' converter never
    # matches the extra '/oee/' or '/downtime/' segment anyway.
    path('machines/<str:device_id>/oee/', MachineOeeView.as_view(), name='machine-oee'),
    path('machines/<str:device_id>/downtime/', MachineDowntimeView.as_view(), name='machine-downtime'),
    path('downtime/top/', TopDowntimeView.as_view(), name='downtime-top'),

    # Endpoint to retrieve detailed telemetry for a specific machine
    # Uses 'device_id' (e.g., "DB-01") instead of the primary key 'id'
    path('machines/<str:device_id>/', MachineDetailView.as_view(), name='machine-detail'),
]