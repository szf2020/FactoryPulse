from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import Machine, SensorReading
from core.seeding import generate_production_history
import random

# Density matters more than range here: calculate_oee()/summarize_downtime()
# only look at events inside the requested window, so a week of continuous,
# near-real-time telemetry is what makes the dashboard's rolling 24h view and
# the assistant's "what's DB-01's OEE this week?" both land on believable,
# internally-consistent numbers — without seeding months of history (and a
# multi-gigabyte database) just to cover every period the API technically
# accepts. Rolling windows wider than this will naturally blend that week of
# real activity with the surrounding silence, the same way they would for any
# line whose monitoring went live recently.
PRODUCTION_HISTORY_DAYS = 7

# One operating "story" per machine — calibrated against core.analytics so
# that each lands at a believable, *different* OEE: a star performer, a solid
# middle-of-the-pack line and one that clearly needs attention. That spread is
# what makes the dashboard and the assistant ("which machine needs the most
# attention?") interesting to look at instead of three identical clones.
PRODUCTION_PROFILES = {
    # ~90% OEE
    "RB-02": dict(performance_target=0.92, scrap_rate=0.010, stoppages_per_day=1, stoppage_minutes=(5, 15)),
    # ~81% OEE
    "DB-01": dict(performance_target=0.85, scrap_rate=0.020, stoppages_per_day=2, stoppage_minutes=(8, 20)),
    # ~67% OEE — the one a plant manager should be worried about
    "CNC-03": dict(performance_target=0.74, scrap_rate=0.045, stoppages_per_day=3, stoppage_minutes=(10, 25)),
}


class Command(BaseCommand):
    """
    Django Management Command to Seed the Database.

    Usage: python manage.py seed_data

    This script populates the database with initial demo data, including:
    1. Machine configurations (Press, Robot, CNC).
    2. Static file references for images.
    3. Mock historical telemetry data for chart visualization.
    4. A week of realistic CYCLE/SCRAP/ERROR_START/ERROR_END history per
       machine, so the OEE and downtime analytics (and the AI layer built on
       top of them) have real numbers to work with instead of zeros.
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

        self.stdout.write(
            f"Generating {PRODUCTION_HISTORY_DAYS} days of production event history "
            "(CYCLE/SCRAP/ERROR_START/ERROR_END)..."
        )
        end = timezone.now()
        start = end - timedelta(days=PRODUCTION_HISTORY_DAYS)
        with transaction.atomic():
            for machine in (m1, m2, m3):
                created = generate_production_history(
                    machine, start, end, **PRODUCTION_PROFILES[machine.device_id]
                )
                self.stdout.write(f"  {machine.device_id}: {created} production events")

        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))