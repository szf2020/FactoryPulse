from django.core.management.base import BaseCommand
from core.models import Machine, SensorReading
from django.utils import timezone
import random

class Command(BaseCommand):
    """
    Django Management Command to Seed the Database.
    
    Usage: python manage.py seed_data

    This script populates the database with initial demo data, including:
    1. Machine configurations (Press, Robot, CNC).
    2. Static file references for images.
    3. Mock historical telemetry data for chart visualization.
    """
    help = 'Populates the database with Test Data and Real Image references.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cleaning up old database records...")
        Machine.objects.all().delete()

        self.stdout.write("Creating test machines...")

        # Machine 1: Hydraulic Press
        m1 = Machine.objects.create(
            name="Hydraulic Press Brake",
            device_id="DB-01",
            machine_type="Press",
            description="High-tonnage press for sheet metal forming.",
            image="machines/dobradeira.jpg", # Ensure this file exists in /media/machines/
            ideal_cycle_time=15.0
        )

        # Machine 2: Welding Robot
        m2 = Machine.objects.create(
            name="Kuka Welding Robot",
            device_id="RB-02",
            machine_type="Automation",
            description="6-axis collaborative robotic arm for MIG/MAG welding.",
            image="machines/robo.jpg",
            ideal_cycle_time=8.0
        )

        # Machine 3: CNC Center (Added for better UI grid layout)
        m3 = Machine.objects.create(
            name="Vertical CNC Center",
            device_id="CNC-03",
            machine_type="CNC",
            description="High precision 3-axis vertical machining center.",
            image="machines/cnc.jpg", 
            ideal_cycle_time=12.0
        )

        self.stdout.write("Generating fake historical energy telemetry...")
        
        # Generate 50 data points (last 50 minutes) for immediate chart visualization
        now = timezone.now()
        for i in range(50):
            time_offset = now - timezone.timedelta(minutes=50-i)
            
            # Press Brake (High energy consumption: 12-18 Amps)
            SensorReading.objects.create(
                machine=m1, 
                timestamp=time_offset, 
                current_amps=random.uniform(12.0, 18.0)
            )
            
            # Robot (Medium energy consumption: 3.5-5.0 Amps)
            SensorReading.objects.create(
                machine=m2, 
                timestamp=time_offset, 
                current_amps=random.uniform(3.5, 5.0)
            )

            # CNC (Variable energy consumption: 8.0-14.0 Amps)
            SensorReading.objects.create(
                machine=m3, 
                timestamp=time_offset, 
                current_amps=random.uniform(8.0, 14.0)
            )

        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))