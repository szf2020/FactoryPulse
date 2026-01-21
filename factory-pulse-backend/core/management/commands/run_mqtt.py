import json
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings
from core.models import Machine, ProductionEvent, SensorReading

class Command(BaseCommand):
    """
    Django Management Command to run the MQTT Worker.
    
    Usage: python manage.py run_mqtt

    This worker acts as a bridge between the IoT Message Broker (Mosquitto)
    and the Django Database. It listens for telemetry data, performs
    edge detection for production events, and logs sensor readings.
    """
    help = 'Starts the MQTT Worker for IoT telemetry ingestion.'

    # In-memory state storage to detect signal edges (Rising/Falling).
    # Used to determine when a signal changes from 0 to 1 (or vice versa).
    _device_states = {}

    def handle(self, *args, **options):
        """
        Main entry point for the command.
        Configures and starts the MQTT blocking loop.
        """
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        self.stdout.write(self.style.SUCCESS(f"Connecting to Broker at {settings.MQTT_BROKER_HOST}..."))
        
        try:
            client.connect(settings.MQTT_BROKER_HOST, settings.MQTT_BROKER_PORT, 60)
            client.loop_forever()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Connection Error: {e}"))

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback executed upon successful connection to the broker.
        Subscribes to the wildcard topic to catch all machine IO data.
        """
        self.stdout.write(self.style.SUCCESS("Connected! Subscribing to industry/+/io"))
        client.subscribe("industry/+/io")

    def on_message(self, client, userdata, msg):
        """
        Callback executed when a message is received.
        Parses JSON, updates machine state, logs energy, and detects OEE events.
        """
        try:
            payload = json.loads(msg.payload.decode())
            device_id = payload.get('id')
            m_type = payload.get('type', 'generic')

            if not device_id: 
                return

            # 1. Machine Provisioning
            # Automatically creates the machine if it does not exist.
            machine, created = Machine.objects.update_or_create(
                device_id=device_id,
                defaults={
                    'name': f"Machine {m_type.upper()}", 
                    'machine_type': m_type
                }
            )

            # 2. Energy Telemetry Logging
            # Logs current amperage for historical analysis.
            amps = float(payload.get('AN1', 0.0))
            SensorReading.objects.create(machine=machine, current_amps=amps)

            # 3. Event Detection (Rising Edge Logic)
            # We compare current payload vs previous state to detect 0->1 transitions.
            last = self._device_states.get(device_id, {})
            
            # DI1: Production Cycle (Good Part)
            if payload.get('DI1') and not last.get('DI1'):
                self.stdout.write(f"[{machine.name}] Part Produced (Cycle End)")
                ProductionEvent.objects.create(machine=machine, event_type='CYCLE')

            # DI4: Scrap/Defect (Bad Part)
            if payload.get('DI4') and not last.get('DI4'):
                self.stdout.write(self.style.WARNING(f"[{machine.name}] SCRAP Detected!"))
                ProductionEvent.objects.create(machine=machine, event_type='SCRAP')

            # DI3: Machine Availability (Error State)
            curr_err = payload.get('DI3')
            prev_err = last.get('DI3')
            
            # Detect Error Start
            if curr_err and not prev_err:
                self.stdout.write(self.style.ERROR(f"[{machine.name}] STOPPAGE (Error Started)"))
                ProductionEvent.objects.create(machine=machine, event_type='ERROR_START')
            
            # Detect Error End (Machine Recovery)
            elif not curr_err and prev_err:
                self.stdout.write(self.style.SUCCESS(f"[{machine.name}] Resuming Operation"))
                ProductionEvent.objects.create(machine=machine, event_type='ERROR_END')

            # Update internal state memory for the next loop
            self._device_states[device_id] = {
                'DI1': payload.get('DI1'),
                'DI3': payload.get('DI3'),
                'DI4': payload.get('DI4')
            }

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Processing Error: {e}"))