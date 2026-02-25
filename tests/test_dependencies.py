from datetime import datetime, timedelta

from taskboard.core.scheduler import generate_schedule
from taskboard.models.task import Task


def make_day(hour):
    return datetime(2026, 1, 1, hour, 0)


def make_task(
    id,
    duration=60,
    priority=2,
    earliest=None,
    latest=None,
    depends_on=None,
    completed=False,
):
    return Task(
        id=id,
        title=f"Task {id}",
        duration_minutes=duration,
        priority=priority,
        earliest_start_time=earliest,
        latest_end_time=latest,
        flexible=False,
        scheduled_date=None,
        depends_on=depends_on or [],
        is_completed=completed,
        work_sessions=[],
        active_session_start=None,
    )


def test_simple_dependency_ordering():
    task_a = make_task(1, duration=60)
    task_b = make_task(2, duration=120, depends_on=[1])

    scheduled, unscheduled = generate_schedule(
        [task_a, task_b],
        events=[],
        day_start=make_day(9),
        day_end=make_day(17),
        buffer_minutes=0,
    )

    assert len(scheduled) == 2

    block_a = next(b for b in scheduled if b.id == 1)
    block_b = next(b for b in scheduled if b.id == 2)

    assert block_b.start_time >= block_a.end_time
    assert not unscheduled


def test_dependency_overrides_priority():
    task_a = make_task(1, duration=60, priority=3)
    task_b = make_task(2, duration=60, priority=1, depends_on=[1])

    scheduled, _ = generate_schedule(
        [task_a, task_b],
        [],
        make_day(9),
        make_day(17),
        buffer_minutes=0,
    )

    block_a = next(b for b in scheduled if b.id == 1)
    block_b = next(b for b in scheduled if b.id == 2)

    assert block_b.start_time >= block_a.end_time


def test_dependency_chain():
    a = make_task(1, 60)
    b = make_task(2, 60, depends_on=[1])
    c = make_task(3, 60, depends_on=[2])

    scheduled, _ = generate_schedule(
        [a, b, c],
        [],
        make_day(9),
        make_day(17),
        buffer_minutes=0,
    )

    blocks = {b.id: b for b in scheduled}

    assert blocks[2].start_time >= blocks[1].end_time
    assert blocks[3].start_time >= blocks[2].end_time


def test_dependency_respects_buffer():
    a = make_task(1, 60)
    b = make_task(2, 60, depends_on=[1])

    scheduled, _ = generate_schedule(
        [a, b],
        [],
        make_day(9),
        make_day(17),
        buffer_minutes=15,
    )

    blocks = {b.id: b for b in scheduled}

    expected_start = blocks[1].end_time + timedelta(minutes=15)
    assert blocks[2].start_time >= expected_start


def test_unschedulable_parent_blocks_child():
    a = make_task(1, duration=600)  # Too long
    b = make_task(2, duration=60, depends_on=[1])

    scheduled, unscheduled = generate_schedule(
        [a, b],
        [],
        make_day(9),
        make_day(12),
        buffer_minutes=0,
    )

    assert any(t.id == 1 for t in unscheduled)
    assert any(t.id == 2 for t in unscheduled)


def test_cross_day_dependency_blocks():
    a = make_task(1, duration=60)
    a.scheduled_date = make_day(10).date() + timedelta(days=1)  # tomorrow

    b = make_task(2, duration=60, depends_on=[1])

    scheduled, unscheduled = generate_schedule(
        [a, b],
        [],
        make_day(9),
        make_day(17),
        buffer_minutes=0,
    )

    assert any(t.id == 2 for t in unscheduled)


def test_circular_dependency():
    a = make_task(1, depends_on=[2])
    b = make_task(2, depends_on=[1])

    scheduled, unscheduled = generate_schedule(
        [a, b],
        [],
        make_day(9),
        make_day(17),
        buffer_minutes=0,
    )

    assert not scheduled
    assert len(unscheduled) == 2
