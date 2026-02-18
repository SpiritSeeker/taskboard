from datetime import datetime, time

import pytest

from taskboard.core.scheduler import generate_schedule
from taskboard.models.task import Task


def make_day(hour: int) -> datetime:
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


@pytest.mark.scheduler
def test_single_task_fits():
    task = make_task()

    schedule, unscheduled = generate_schedule([task], make_day(9), make_day(17))

    assert len(schedule) == 1
    assert len(unscheduled) == 0

    block = schedule[0]
    assert block.start_time == make_day(9)
    assert block.end_time == make_day(10)


@pytest.mark.scheduler
def test_respects_time_window():
    task = make_task(
        earliest_start_time=time(13, 0),
        latest_end_time=time(15, 0),
    )

    schedule, _ = generate_schedule([task], make_day(9), make_day(17))

    block = schedule[0]
    assert block.start_time.hour >= 13
    assert block.end_time.hour <= 15


@pytest.mark.scheduler
def test_overflow_unscheduled():
    long_task = make_task(duration_minutes=600)  # 10 hours

    schedule, unscheduled = generate_schedule([long_task], make_day(9), make_day(17))

    assert len(schedule) == 0
    assert len(unscheduled) == 1


@pytest.mark.scheduler
def test_priority_ordering():
    high = make_task(id=1, priority=1)
    low = make_task(id=2, priority=3)

    schedule, _ = generate_schedule(
        [low, high],
        day_start=make_day(9),
        day_end=make_day(17),
    )

    assert schedule[0].task == high
    assert schedule[1].task == low


@pytest.mark.scheduler
def test_no_overlap():
    t1 = make_task(id=1, duration_minutes=120)
    t2 = make_task(id=2, duration_minutes=120)

    schedule, _ = generate_schedule(
        [t1, t2],
        day_start=make_day(9),
        day_end=make_day(17),
    )

    assert schedule[0].end_time <= schedule[1].start_time


@pytest.mark.scheduler
def test_buffer_between_tasks():
    t1 = make_task(id=1, duration_minutes=60)
    t2 = make_task(id=2, duration_minutes=60)

    schedule, _ = generate_schedule(
        [t1, t2],
        day_start=make_day(9),
        day_end=make_day(17),
        buffer_minutes=10,
    )

    assert schedule[0].end_time.minute == 0
    assert schedule[1].start_time.minute == 10
