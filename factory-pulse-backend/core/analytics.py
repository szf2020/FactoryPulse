"""
Reusable analytics helpers for OEE and downtime calculations.

Centralizes the logic that originally lived inline in MachineDetailView so it
can be shared across the machine detail, OEE-by-period and downtime endpoints
(and, ultimately, the AI layer that consumes the read-only API).
"""
import re
from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError

# MVP heuristic kept from the original real-time OEE calculation: each
# ERROR_START is assumed to represent a fixed-length stoppage.
SECONDS_PER_ERROR_START = 300

PERIOD_PATTERN = re.compile(r'^(\d+)(m|h|d)$')
PERIOD_UNITS = {'m': 'minutes', 'h': 'hours', 'd': 'days'}


def resolve_period(period, default='24h'):
    """
    Converts a period string (e.g. "30m", "24h", "7d") into a (start, end)
    datetime range ending at the current time. Raises ValidationError (DRF)
    for unsupported formats so views can surface a clean 400 response.
    """
    raw = (period or default).strip().lower()
    match = PERIOD_PATTERN.match(raw)
    if not match:
        raise ValidationError(
            f"Invalid period '{period}'. Use formats like '30m', '24h' or '7d'."
        )

    amount, unit = match.groups()
    end = timezone.now()
    start = end - timedelta(**{PERIOD_UNITS[unit]: int(amount)})
    return start, end


def calculate_oee(machine, start, end):
    """
    Calculates Availability, Performance, Quality and the global OEE score
    for a machine within [start, end], reusing the same MVP heuristics as the
    original dashboard calculation (5 minutes of downtime per ERROR_START).
    """
    events = machine.events.filter(timestamp__gte=start, timestamp__lte=end)
    total_seconds = (end - start).total_seconds()

    downtime_seconds = events.filter(event_type='ERROR_START').count() * SECONDS_PER_ERROR_START
    run_time = max(0, total_seconds - downtime_seconds)
    availability = (run_time / total_seconds) * 100 if total_seconds > 0 else 0

    total_produced = events.filter(event_type='CYCLE').count()
    if run_time > 0 and machine.ideal_cycle_time > 0:
        theoretical_max = run_time / machine.ideal_cycle_time
        performance = (total_produced / theoretical_max) * 100 if theoretical_max > 0 else 0
    else:
        performance = 0

    total_scraps = events.filter(event_type='SCRAP').count()
    good_parts = max(0, total_produced - total_scraps)
    quality = (good_parts / total_produced) * 100 if total_produced > 0 else 100

    oee_score = (availability * performance * quality) / 10000

    return {
        "availability": round(availability, 1),
        "performance": round(performance, 1),
        "quality": round(quality, 1),
        "global": round(oee_score, 1),
    }


def list_stoppages(machine, start, end):
    """
    Pairs ERROR_START/ERROR_END events within [start, end] into discrete
    stoppage intervals with measured durations. A stoppage that started
    before 'end' but has no matching ERROR_END yet is reported as ongoing,
    with its duration measured up to 'end'.
    """
    events = machine.events.filter(
        event_type__in=['ERROR_START', 'ERROR_END'],
        timestamp__gte=start,
        timestamp__lte=end,
    ).order_by('timestamp')

    stoppages = []
    open_start = None
    for event in events:
        if event.event_type == 'ERROR_START':
            open_start = event.timestamp
        elif event.event_type == 'ERROR_END' and open_start is not None:
            stoppages.append({
                "start": open_start,
                "end": event.timestamp,
                "duration_seconds": (event.timestamp - open_start).total_seconds(),
                "ongoing": False,
            })
            open_start = None

    if open_start is not None:
        stoppages.append({
            "start": open_start,
            "end": None,
            "duration_seconds": (end - open_start).total_seconds(),
            "ongoing": True,
        })

    return stoppages


def summarize_downtime(machine, start, end):
    """Returns the stoppage list plus aggregate totals for a machine/period."""
    stoppages = list_stoppages(machine, start, end)
    return {
        "stoppage_count": len(stoppages),
        "total_downtime_seconds": sum(s["duration_seconds"] for s in stoppages),
        "stoppages": stoppages,
    }
