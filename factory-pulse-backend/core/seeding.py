"""
Reusable helpers for generating realistic ProductionEvent timelines.

Centralizes the "what would a week of shop-floor activity actually look like"
logic in one dependency-light module so it can be exercised directly from
tests and reused by management commands — the same separation core.analytics
keeps between OEE math and the views that serve it.
"""
import random
from datetime import timedelta

from .models import ProductionEvent

# MVP heuristic shared with core.analytics: each ERROR_START is treated as a
# fixed-length stoppage, so a handful of short, well-spaced windows is enough
# to give get_downtime()/top_downtime() real intervals to report without the
# noise of overlapping or back-to-back stoppages.
MIN_STOPPAGE_GAP_ATTEMPTS_PER_TARGET = 25


def plan_stoppages(start, end, stoppages_per_day, stoppage_minutes):
    """
    Picks a handful of non-overlapping (start, end) windows spread across
    [start, end) to stand in for unplanned stoppages. Returns them sorted
    chronologically so callers can walk a timeline and the planned windows
    in lockstep.
    """
    span = (end - start).total_seconds()
    target_count = max(1, round(stoppages_per_day * span / 86400))

    stoppages = []
    attempts = 0
    max_attempts = target_count * MIN_STOPPAGE_GAP_ATTEMPTS_PER_TARGET
    while len(stoppages) < target_count and attempts < max_attempts:
        attempts += 1
        candidate_start = start + timedelta(seconds=random.uniform(0, span))
        candidate_end = candidate_start + timedelta(minutes=random.uniform(*stoppage_minutes))
        if candidate_end >= end:
            continue
        if any(candidate_start < s_end and candidate_end > s_start for s_start, s_end in stoppages):
            continue
        stoppages.append((candidate_start, candidate_end))

    return sorted(stoppages)


def generate_production_history(machine, start, end, *, performance_target,
                                 scrap_rate, stoppages_per_day, stoppage_minutes):
    """
    Builds and persists a realistic CYCLE/SCRAP/ERROR_START/ERROR_END timeline
    for `machine` covering [start, end), paced so that
    core.analytics.calculate_oee() lands close to `performance_target` for any
    sub-window of [start, end). Returns the number of events created.

    ProductionEvent.timestamp uses auto_now_add, which stamps every row with
    "now" regardless of what's passed at creation time — the same problem the
    _backdate() helper in core/tests.py works around for one-off fixtures. At
    the volume a multi-day timeline needs, looping a queryset .update() per
    event would be far too slow, so events are bulk_created first (auto_now_add
    fires once, harmlessly) and every timestamp is rewritten in one bulk_update.
    """
    stoppages = plan_stoppages(start, end, stoppages_per_day, stoppage_minutes)

    events = []
    timestamps = []

    # Calibrated so that, on average, CYCLE_count / (run_time / ideal_cycle_time)
    # — exactly what calculate_oee() computes as "performance" — converges on
    # performance_target, even though a slice of attempts become SCRAP instead
    # of CYCLE (and only CYCLE events count towards "produced").
    interval = machine.ideal_cycle_time * (1 - scrap_rate) / performance_target

    cursor = start
    pending = iter(stoppages)
    next_stoppage = next(pending, None)
    while cursor < end:
        if next_stoppage and cursor >= next_stoppage[0]:
            cursor = next_stoppage[1]
            next_stoppage = next(pending, None)
            continue

        event_type = 'SCRAP' if random.random() < scrap_rate else 'CYCLE'
        events.append(ProductionEvent(machine=machine, event_type=event_type))
        timestamps.append(cursor)
        cursor += timedelta(seconds=interval * random.uniform(0.8, 1.2))

    for stoppage_start, stoppage_end in stoppages:
        events.append(ProductionEvent(machine=machine, event_type='ERROR_START'))
        timestamps.append(stoppage_start)
        events.append(ProductionEvent(machine=machine, event_type='ERROR_END'))
        timestamps.append(stoppage_end)

    created = ProductionEvent.objects.bulk_create(events, batch_size=2000)
    for event, when in zip(created, timestamps):
        event.timestamp = when
    ProductionEvent.objects.bulk_update(created, ['timestamp'], batch_size=2000)

    return len(created)
