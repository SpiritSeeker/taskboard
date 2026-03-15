from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from taskboard.core.timeline import ScheduledBlock
from taskboard.models.event import Event
from taskboard.models.task import Task

FreeInterval = Tuple[datetime, datetime]


def generate_schedule(
    tasks: List[Task],
    events: List[Event],
    day_start: datetime,
    day_end: datetime,
    buffer_minutes: int = 0,
) -> Tuple[List[ScheduledBlock], List[Task]]:
    scheduled_blocks: List[ScheduledBlock] = []
    unscheduled_tasks: List[Task] = []

    task_map = {t.id: t for t in tasks}
    scheduled_task_ids: Set[int] = set()
    scheduled_blocks_map: Dict[int, ScheduledBlock] = {}
    remaining_tasks = tasks.copy()

    today_date = day_start.date()

    # Remove active task from scheduling pool and add it as a scheduled block
    _handle_active_task(
        tasks,
        scheduled_blocks,
        scheduled_blocks_map,
        scheduled_task_ids,
        remaining_tasks,
        day_start,
        buffer_minutes,
    )

    # Create free intervals for the day and block out events
    free_intervals: List[FreeInterval] = [(day_start, day_end)]
    buffer = timedelta(minutes=buffer_minutes)
    free_intervals = _apply_event_blocking(free_intervals, events, today_date, buffer)

    # Filter incomplete tasks that are scheduled for today or have no scheduled date
    remaining_tasks = [
        t
        for t in remaining_tasks
        if not t.is_completed
        and (t.scheduled_date is None or t.scheduled_date <= today_date)
    ]

    # Main scheduling loop
    while remaining_tasks:
        # Get eligible tasks that are not blocked by dependencies
        eligible_tasks = _get_eligible_tasks(
            remaining_tasks, task_map, scheduled_task_ids
        )

        if not eligible_tasks:
            unscheduled_tasks.extend(remaining_tasks)
            break

        # Sort eligible tasks by flexible, priority, latest_end_time, and duration
        sorted_tasks = sorted(
            eligible_tasks,
            key=lambda t: (
                t.flexible,
                t.priority,
                t.latest_end_time or datetime.min.time(),
                -t.duration_minutes,
            ),
        )

        # Try to place the highest priority eligible task
        task = sorted_tasks[0]
        placed_block = _try_place_task(
            task,
            free_intervals,
            scheduled_blocks,
            scheduled_blocks_map,
            day_start,
            buffer,
        )

        # If the task was placed, add it to the schedule and mark it as scheduled
        if placed_block:
            scheduled_blocks.append(placed_block)
            scheduled_task_ids.add(task.id)
            scheduled_blocks_map[task.id] = placed_block
        else:
            unscheduled_tasks.append(task)

        remaining_tasks.remove(task)

    # Sort scheduled blocks by start time
    scheduled_blocks.sort(key=lambda block: block.start_time)

    return scheduled_blocks, unscheduled_tasks


def _get_eligible_tasks(
    remaining_tasks: List[Task], task_map: Dict[int, Task], scheduled_task_ids: Set[int]
) -> List[Task]:
    eligible_tasks: List[Task] = []

    for task in remaining_tasks:
        deps = task.depends_on
        blocked = False
        for dep_id in deps:
            dep_task = task_map.get(dep_id)

            if not dep_task:
                continue

            if not dep_task.is_completed and dep_id not in scheduled_task_ids:
                blocked = True
                break

        if not blocked:
            eligible_tasks.append(task)
    return eligible_tasks


def _apply_event_blocking(
    free_intervals: List[FreeInterval],
    events: List[Event],
    today_date,
    buffer: timedelta,
) -> List[FreeInterval]:
    # Block events and update free intervals
    events_sorted = sorted(events, key=lambda e: e.start)
    for event in events_sorted:
        if event.start.date() != today_date:
            continue

        new_intervals = []
        for free_start, free_end in free_intervals:
            # No overlap
            if event.end <= free_start or event.start >= free_end:
                new_intervals.append((free_start, free_end))
                continue

            # Before event
            buffered_start = event.start - buffer
            if free_start < buffered_start:
                new_intervals.append((free_start, buffered_start))

            # After event
            buffered_end = event.end + buffer
            if buffered_end < free_end:
                new_intervals.append((buffered_end, free_end))

        free_intervals = sorted(new_intervals, key=lambda x: x[0])
    return free_intervals


def _try_place_task(
    task: Task,
    free_intervals: List[FreeInterval],
    scheduled_blocks: List[ScheduledBlock],
    scheduled_blocks_map: Dict[int, ScheduledBlock],
    day_start: datetime,
    buffer: timedelta,
) -> Optional[ScheduledBlock]:
    duration = timedelta(minutes=task.duration_minutes)

    effective_task_start = (
        datetime.combine(day_start.date(), task.earliest_start_time)
        if task.earliest_start_time
        else day_start
    )
    for dep_id in task.depends_on:
        if dep_id in scheduled_blocks_map:
            dep_block = scheduled_blocks_map[dep_id]
            effective_task_start = max(effective_task_start, dep_block.end_time)

    for i, (free_start, free_end) in enumerate(free_intervals):
        window_start = free_start
        window_end = free_end

        if effective_task_start:
            window_start = max(
                free_start,
                effective_task_start,
            )
        if task.latest_end_time:
            window_end = min(
                free_end,
                datetime.combine(day_start.date(), task.latest_end_time),
            )

        if window_end <= window_start:
            continue

        if window_end - window_start >= duration:
            start_time = window_start
            end_time = start_time + duration

            # Ensure end_time + buffer does not go into another scheduled block
            if buffer > timedelta(0):
                for block in scheduled_blocks:
                    if (
                        block.start_time < end_time + buffer
                        and block.end_time > end_time
                    ):
                        return None

            placed_block = ScheduledBlock(
                id=task.id,
                title=task.title,
                start_time=start_time,
                end_time=end_time,
            )

            # Update free intervals
            new_intervals = []

            # Before block
            if free_start < start_time:
                new_intervals.append((free_start, start_time))

            # Buffer interval
            buffered_end = end_time + buffer

            # After block
            if buffered_end < free_end:
                new_intervals.append((buffered_end, free_end))

            # Replace the current free interval with the new ones
            free_intervals.pop(i)
            free_intervals.extend(new_intervals)

            # Keep intervals sorted
            free_intervals.sort(key=lambda x: x[0])

            return placed_block

    return None


def _handle_active_task(
    tasks: List[Task],
    scheduled_blocks: List[ScheduledBlock],
    scheduled_blocks_map: Dict[int, ScheduledBlock],
    scheduled_task_ids: Set[int],
    remaining_tasks: List[Task],
    day_start: datetime,
    buffer_minutes: int,
) -> None:
    # Detect active task
    active_tasks = [
        task
        for task in tasks
        if getattr(task, "active_session_start", None) is not None
    ]
    if active_tasks:
        active_task = active_tasks[0]
        assert active_task.active_session_start is not None
        active_task_end_estimated = active_task.active_session_start + timedelta(
            minutes=active_task.duration_minutes
        )
        # If the active task end time is in the past, the active task end time is now
        if active_task_end_estimated < datetime.now():
            active_task_end_estimated = datetime.now()

        # Bump the active_task_end_estimated to next multiple of buffer_minutes if buffer is set
        if buffer_minutes > 0:
            buffer_td = timedelta(minutes=buffer_minutes)
            active_task_end_estimated += (
                buffer_td - (active_task_end_estimated - datetime.min) % buffer_td
            ) % buffer_td
            day_start = max(day_start, active_task_end_estimated + buffer_td)
        else:
            day_start = max(day_start, active_task_end_estimated)

        active_block = ScheduledBlock(
            id=active_task.id,
            title=active_task.title + " (IN PROGRESS)",
            start_time=active_task.active_session_start,
            end_time=active_task_end_estimated,
        )
        scheduled_blocks.append(active_block)

        # Remove active task from scheduling pool
        remaining_tasks.remove(active_task)
        scheduled_task_ids.add(active_task.id)
        scheduled_blocks_map[active_task.id] = active_block
