from django.urls import path
from .views import MachineListView, MachineDetailView

urlpatterns = [
    # Endpoint to list all machines (Summary View)
    path('machines/', MachineListView.as_view(), name='machine-list'),

    # Endpoint to retrieve detailed telemetry for a specific machine
    # Uses 'device_id' (e.g., "DB-01") instead of the primary key 'id'
    path('machines/<str:device_id>/', MachineDetailView.as_view(), name='machine-detail'),
]