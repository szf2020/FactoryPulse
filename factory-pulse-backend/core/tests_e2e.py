"""
End-to-end coverage for the read-only analytics endpoints that back the AI
layer (MCP server + assistant + chat widget).

AnalyticsEndpointsTests (core/tests.py) already proves the view/serializer/
analytics wiring through Django's in-process test client — that's the right
tool for fast, focused checks. What it can't exercise is the actual boundary
those AI integrations cross every time they run: a real TCP connection, a real
HTTP server parsing a real `Authorization` header, against a database holding
a realistic week of telemetry rather than a handful of hand-placed events.
LiveServerTestCase spins up exactly that — a live instance of this API on a
real socket — and the standard library's urlopen plays the part of the
external client (the same role factorypulse_mcp.client.FactoryPulseClient
plays in production), so this suite is the genuine end-to-end counterpart.
"""
import json
from datetime import timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.contrib.auth.models import User
from django.test import LiveServerTestCase
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Machine
from .seeding import generate_production_history


class AnalyticsLiveServerE2ETests(LiveServerTestCase):
    """Read-only analytics endpoints, exercised over a live HTTP connection."""

    def setUp(self):
        # TransactionTestCase truncates tables between tests, so fixtures live
        # in setUp (recreated per test) rather than setUpClass.
        self.user = User.objects.create_user(username='e2e-reader', password='pass12345')
        self.token = str(RefreshToken.for_user(self.user).access_token)

        self.machine = Machine.objects.create(
            name="E2E Test Press",
            device_id="E2E-01",
            machine_type="Press",
            ideal_cycle_time=10.0,
        )

        # calculate_oee measures performance against the *full* requested
        # window, not just the span that has data — so the seeded history
        # must cover the same 24h the tests query, or the numbers get
        # diluted (e.g. 6h of real activity inside a 24h window reads as
        # ~1/4 of the requested performance_target).
        end = timezone.now()
        start = end - timedelta(hours=24)
        generate_production_history(
            self.machine, start, end,
            performance_target=0.8, scrap_rate=0.02,
            stoppages_per_day=3, stoppage_minutes=(5, 15),
        )

    def _get(self, path, token=None):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = Request(f"{self.live_server_url}{path}", headers=headers)
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read())

    def test_oee_endpoint_returns_realistic_numbers_over_a_live_connection(self):
        status_code, payload = self._get(
            f"/api/machines/{self.machine.device_id}/oee/?period=24h", token=self.token
        )

        self.assertEqual(status_code, 200)
        oee = payload["oee"]
        self.assertEqual(set(oee.keys()), {"availability", "performance", "quality", "global"})
        # Same tolerance as ProductionHistorySeedingTests: jitter and the
        # SECONDS_PER_ERROR_START heuristic mean it won't be exact, only
        # believable — which is the whole point of seeding it this way.
        self.assertAlmostEqual(oee["performance"], 80.0, delta=10)
        self.assertGreater(oee["availability"], 80.0)

    def test_downtime_endpoint_reports_real_stoppages_over_a_live_connection(self):
        status_code, payload = self._get(
            f"/api/machines/{self.machine.device_id}/downtime/?period=24h", token=self.token
        )

        self.assertEqual(status_code, 200)
        self.assertGreater(payload["stoppage_count"], 0)
        self.assertGreater(payload["total_downtime_seconds"], 0)
        for stoppage in payload["stoppages"]:
            self.assertIn(stoppage["ongoing"], (True, False))

    def test_top_downtime_ranking_includes_the_seeded_machine(self):
        status_code, payload = self._get("/api/downtime/top/?period=24h&limit=5", token=self.token)

        self.assertEqual(status_code, 200)
        machine_ids = [entry["machine"] for entry in payload["ranking"]]
        self.assertIn(self.machine.device_id, machine_ids)

    def test_request_without_a_token_is_rejected_over_a_live_connection(self):
        with self.assertRaises(HTTPError) as raised:
            self._get(f"/api/machines/{self.machine.device_id}/oee/?period=24h")

        self.assertEqual(raised.exception.code, 401)
