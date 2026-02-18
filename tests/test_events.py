from datetime import datetime, time, timedelta

import pytest

from taskboard.core.scheduler import generate_schedule
from taskboard.models.event import Event
from taskboard.models.task import Task


def make_day(hour):
    return datetime(2026, 1, 1, hour, 0)


def make_task(
    id=1,
    title="Task",
    duration_minutes=60,
    priority=1,
    earliest_start_time=None,
    latest_end_time=None,
    flexible=False,
) -> Task:
    return Task(
        id=id,
        title=title,
        duration_minutes=duration_minutes,
        priority=priority,
        earliest_start_time=earliest_start_time,
        latest_end_time=latest_end_time,
        flexible=flexible,
    )


def make_event(id=2, start_hour=14, end_hour=15):
    return Event(
        id=id,
        title="Event",
        start=make_day(start_hour),
        end=make_day(end_hour),
        source="manual",
    )


@pytest.mark.scheduler
def test_event_blocks_time():
    task = make_task(duration_minutes=120)
    event = make_event(14, 15)

    schedule, _ = generate_schedule(
        [task],
        [event],
        day_start=make_day(12),
        day_end=make_day(18),
        buffer_minutes=0,
    )

    for block in schedule:
        assert not (block.start_time < event.end and block.end_time > event.start)


@pytest.mark.scheduler
def test_buffer_after_event():
    task = make_task(duration_minutes=165)
    event = make_event(14, 15)

    schedule, _ = generate_schedule(
        [task],
        [event],
        day_start=make_day(13),
        day_end=make_day(18),
        buffer_minutes=15,
    )

    task_block = schedule[0]

    assert task_block.start_time >= make_day(15) + timedelta(minutes=15)


@pytest.mark.scheduler
def test_buffer_before_event():
    task = make_task(duration_minutes=105)
    event = make_event(14, 15)

    schedule, _ = generate_schedule(
        [task],
        [event],
        day_start=make_day(12),
        day_end=make_day(18),
        buffer_minutes=15,
    )

    task_block = schedule[0]

    assert task_block.end_time <= make_day(14) - timedelta(minutes=15)


@pytest.mark.scheduler
def test_tight_window_with_event_and_buffer():
    taskA = make_task(
        id=1,
        duration_minutes=120,
        priority=1,
        earliest_start_time=time(12, 0),
        latest_end_time=time(20, 0),
    )

    eventB = Event(
        id=2,
        title="Event B",
        start=make_day(14),
        end=make_day(16),
        source="manual",
    )

    schedule, unscheduled = generate_schedule(
        [taskA],
        [eventB],
        day_start=make_day(12),
        day_end=make_day(20),
        buffer_minutes=15,
    )

    assert schedule[0].start_time >= make_day(16) + timedelta(minutes=15)
    assert len(unscheduled) == 0


@pytest.mark.scheduler
def test_multiple_events_split_day():
    task = make_task(duration_minutes=60)

    event1 = make_event(13, 14)
    event2 = make_event(16, 17)

    schedule, _ = generate_schedule(
        [task],
        [event1, event2],
        day_start=make_day(12),
        day_end=make_day(18),
        buffer_minutes=0,
    )

    # Task must fit in one of the free gaps
    valid_slots = [
        (make_day(12), make_day(13)),
        (make_day(14), make_day(16)),
        (make_day(17), make_day(18)),
    ]

    task_block = schedule[0]

    assert any(
        start <= task_block.start_time and task_block.end_time <= end
        for start, end in valid_slots
    )


@pytest.mark.scheduler
def test_events_never_unscheduled():
    task = make_task(duration_minutes=360)
    event = make_event(14, 15)

    schedule, unscheduled = generate_schedule(
        [task],
        [event],
        day_start=make_day(12),
        day_end=make_day(18),
        buffer_minutes=0,
    )

    # Only task can be unscheduled
    assert all(t.id != event.id for t in unscheduled)


@pytest.mark.scheduler
def test_no_overlap_any_blocks():
    task1 = make_task(id=1, duration_minutes=60)
    task2 = make_task(id=2, duration_minutes=60)
    event = make_event(id=3, start_hour=14, end_hour=15)

    schedule, _ = generate_schedule(
        [task1, task2],
        [event],
        day_start=make_day(12),
        day_end=make_day(18),
        buffer_minutes=15,
    )

    for i in range(len(schedule) - 1):
        assert schedule[i].end_time <= schedule[i + 1].start_time
