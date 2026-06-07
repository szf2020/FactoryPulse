from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Machine, ProductionEvent


def _backdate(event, when):
    """
    ProductionEvent.timestamp uses auto_now_add, which ignores any value
    passed at creation time. Bypass it via a queryset update (no save()
    call) so tests can build deterministic timelines.
    """
    ProductionEvent.objects.filter(pk=event.pk).update(timestamp=when)


class AnalyticsEndpointsTests(APITestCase):
    """
    Covers the read-only analytics endpoints added for the AI layer:
    OEE-by-period, downtime-by-period and top-downtime ranking.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass12345')
        self.client.force_authenticate(user=self.user)

        self.machine = Machine.objects.create(
            name="Test Press",
            device_id="TEST-01",
            machine_type="Press",
            ideal_cycle_time=10.0,
        )

        self.now = timezone.now()

        # One closed stoppage of exactly 10 minutes, well inside the period
        start_evt = ProductionEvent.objects.create(machine=self.machine, event_type='ERROR_START')
        _backdate(start_evt, self.now - timedelta(hours=2))
        end_evt = ProductionEvent.objects.create(machine=self.machine, event_type='ERROR_END')
        _backdate(end_evt, self.now - timedelta(hours=2) + timedelta(minutes=10))

        # Production cycles + one scrap, used to assert the OEE quality figure
        for offset in (90, 80, 70, 60):
            evt = ProductionEvent.objects.create(machine=self.machine, event_type='CYCLE')
            _backdate(evt, self.now - timedelta(minutes=offset))
        scrap = ProductionEvent.objects.create(machine=self.machine, event_type='SCRAP')
        _backdate(scrap, self.now - timedelta(minutes=65))

    # --- OEE by period -------------------------------------------------

    def test_oee_endpoint_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(f'/api/machines/{self.machine.device_id}/oee/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_oee_endpoint_returns_breakdown_for_period(self):
        response = self.client.get(
            f'/api/machines/{self.machine.device_id}/oee/', {'period': '24h'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        oee = response.data['oee']
        self.assertEqual(set(oee.keys()), {'availability', 'performance', 'quality', 'global'})
        # 4 good-part cycles and 1 scrap -> quality = (4 - 1) / 4 * 100
        self.assertEqual(oee['quality'], 75.0)

    def test_oee_endpoint_rejects_invalid_period(self):
        response = self.client.get(
            f'/api/machines/{self.machine.device_id}/oee/', {'period': 'not-a-period'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_oee_endpoint_404_for_unknown_machine(self):
        response = self.client.get('/api/machines/UNKNOWN/oee/', {'period': '24h'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- Downtime by period --------------------------------------------

    def test_downtime_endpoint_pairs_start_and_end_events(self):
        response = self.client.get(
            f'/api/machines/{self.machine.device_id}/downtime/', {'period': '24h'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['stoppage_count'], 1)
        stoppage = response.data['stoppages'][0]
        self.assertFalse(stoppage['ongoing'])
        self.assertIsNotNone(stoppage['end'])
        self.assertAlmostEqual(stoppage['duration_seconds'], 600, delta=1)

    def test_downtime_endpoint_reports_ongoing_stoppage(self):
        evt = ProductionEvent.objects.create(machine=self.machine, event_type='ERROR_START')
        _backdate(evt, self.now - timedelta(minutes=5))

        response = self.client.get(
            f'/api/machines/{self.machine.device_id}/downtime/', {'period': '24h'}
        )

        ongoing = [s for s in response.data['stoppages'] if s['ongoing']]
        self.assertEqual(len(ongoing), 1)
        self.assertIsNone(ongoing[0]['end'])
        self.assertAlmostEqual(ongoing[0]['duration_seconds'], 300, delta=2)

    # --- Top downtime ranking -------------------------------------------

    def test_top_downtime_ranks_machines_by_total_downtime(self):
        quiet_machine = Machine.objects.create(
            name="Quiet CNC", device_id="TEST-02", machine_type="CNC"
        )

        response = self.client.get('/api/downtime/top/', {'period': '24h', 'limit': 5})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ranking = response.data['ranking']
        machine_ids = [item['machine'] for item in ranking]

        self.assertIn(self.machine.device_id, machine_ids)
        self.assertIn(quiet_machine.device_id, machine_ids)
        # The machine with the recorded stoppage must lead the ranking
        self.assertEqual(ranking[0]['machine'], self.machine.device_id)
        self.assertEqual(ranking[0]['total_downtime_seconds'], 600)
