from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .analytics import calculate_oee, summarize_downtime
from .models import Machine, ProductionEvent
from .seeding import generate_production_history, plan_stoppages


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

    # --- Machine list snapshot ------------------------------------------

    def test_machine_list_returns_live_oee_snapshot(self):
        response = self.client.get('/api/machines/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        listed = next(m for m in response.data if m['device_id'] == self.machine.device_id)
        oee = listed['oee']
        self.assertEqual(set(oee.keys()), {'availability', 'performance', 'quality', 'global'})
        # Same fixture as test_oee_endpoint_returns_breakdown_for_period: 4
        # good-part cycles and 1 scrap inside the last 24h, so quality stays
        # deterministic regardless of the exact instant `now` is evaluated —
        # unlike the old OeeData snapshot, which always defaulted every field
        # (including quality and availability) to 0.0.
        self.assertEqual(oee['quality'], 75.0)
        self.assertGreater(oee['availability'], 0)

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


class ProductionHistorySeedingTests(TestCase):
    """
    Covers core.seeding.generate_production_history — the helper behind
    seed_data that turns a (machine, profile) pair into a believable
    CYCLE/SCRAP/ERROR_START/ERROR_END timeline. The bar for "realistic" here
    is concrete: feed the generated timeline back through core.analytics and
    the numbers it returns should land close to what the profile asked for —
    that's exactly what makes the demo data (and the AI layer reasoning over
    it) worth looking at instead of a wall of zeros.
    """

    def setUp(self):
        self.machine = Machine.objects.create(
            name="Seed Test Press",
            device_id="SEED-01",
            machine_type="Press",
            ideal_cycle_time=10.0,
        )
        self.end = timezone.now()
        self.start = self.end - timedelta(hours=6)

    def test_generates_events_only_within_the_requested_window(self):
        generate_production_history(
            self.machine, self.start, self.end,
            performance_target=0.8, scrap_rate=0.02,
            stoppages_per_day=2, stoppage_minutes=(5, 15),
        )

        timestamps = list(self.machine.events.values_list('timestamp', flat=True))
        self.assertTrue(timestamps)
        self.assertTrue(all(self.start <= ts <= self.end for ts in timestamps))

    def test_oee_lands_close_to_the_requested_profile(self):
        generate_production_history(
            self.machine, self.start, self.end,
            performance_target=0.8, scrap_rate=0.02,
            stoppages_per_day=2, stoppage_minutes=(5, 15),
        )

        oee = calculate_oee(self.machine, self.start, self.end)
        # Random jitter and the SECONDS_PER_ERROR_START heuristic mean these
        # won't match the inputs exactly — landing in the same ballpark is all
        # the demo data needs to look believable.
        self.assertAlmostEqual(oee['performance'], 80.0, delta=8)
        self.assertAlmostEqual(oee['quality'], 98.0, delta=2)
        self.assertGreater(oee['availability'], 90.0)

    def test_includes_real_stoppages_for_the_downtime_views(self):
        generate_production_history(
            self.machine, self.start, self.end,
            performance_target=0.8, scrap_rate=0.0,
            stoppages_per_day=4, stoppage_minutes=(5, 15),
        )

        downtime = summarize_downtime(self.machine, self.start, self.end)
        self.assertGreater(downtime['stoppage_count'], 0)
        for stoppage in downtime['stoppages']:
            self.assertFalse(stoppage['ongoing'])
            self.assertTrue(5 * 60 <= stoppage['duration_seconds'] <= 15 * 60)


class StoppagePlanningTests(TestCase):
    """core.seeding.plan_stoppages — the scheduling half of the timeline."""

    def setUp(self):
        self.end = timezone.now()
        self.start = self.end - timedelta(days=2)

    def test_plans_non_overlapping_chronological_windows_inside_the_period(self):
        stoppages = plan_stoppages(self.start, self.end, stoppages_per_day=3, stoppage_minutes=(5, 20))

        self.assertTrue(stoppages)
        previous_end = self.start
        for window_start, window_end in stoppages:
            self.assertGreaterEqual(window_start, previous_end)
            self.assertLess(window_start, window_end)
            self.assertLess(window_end, self.end)
            previous_end = window_end

    def test_plans_roughly_the_requested_number_per_day(self):
        stoppages = plan_stoppages(self.start, self.end, stoppages_per_day=3, stoppage_minutes=(5, 10))

        # 3/day over a 2-day window -> 6 targeted; short windows leave plenty
        # of room, so the planner should comfortably hit its target.
        self.assertEqual(len(stoppages), 6)
