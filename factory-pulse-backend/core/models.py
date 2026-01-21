from django.db import models

class Machine(models.Model):
    """
    Represents an industrial machine or asset in the factory.
    Acts as the parent entity for all telemetry and OEE data.
    """
    name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=50, unique=True, db_index=True)
    machine_type = models.CharField(max_length=50, default="Generic")
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='machines/', blank=True, null=True)
    
    # Target KPIs (Benchmarks)
    ideal_cycle_time = models.FloatField(default=10.0, help_text="Ideal cycle time in seconds per part.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.device_id})"


class OeeData(models.Model):
    """
    Stores calculated OEE (Overall Equipment Effectiveness) metrics for a machine.
    This model usually has a One-to-One relationship as it represents the *current* state.
    """
    # 'related_name="oee"' is crucial for the Serializer to access this data via 'machine.oee'
    machine = models.OneToOneField(Machine, on_delete=models.CASCADE, related_name='oee')
    
    availability = models.FloatField(default=0.0)
    performance = models.FloatField(default=0.0)
    quality = models.FloatField(default=0.0)
    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OEE Status: {self.machine.name}"


class ProductionEvent(models.Model):
    """
    Log of discrete operational events detected by the IoT Gateway.
    Used to calculate Performance (Cycles) and Quality (Scrap).
    """
    EVENT_TYPES = [
        ('CYCLE', 'Good Part'),
        ('SCRAP', 'Scrap/Defect'),
        ('ERROR_START', 'Stoppage Start'),
        ('ERROR_END', 'Stoppage End'),
    ]

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.machine.name} - {self.event_type}"


class SensorReading(models.Model):
    """
    High-frequency telemetry data (Time-Series).
    Used for plotting charts (e.g., Energy Consumption over time).
    """
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='readings')
    timestamp = models.DateTimeField(auto_now_add=True)
    current_amps = models.FloatField(help_text="Motor Current in Amperes")

    def __str__(self):
        return f"{self.machine.name} - {self.current_amps}A"