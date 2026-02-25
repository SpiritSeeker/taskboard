from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple

from taskboard.core.timeline import ScheduledBlock
from taskboard.models.event import Event
from taskboard.models.task import Task

FreeInverval = Tuple[datetime, datetime]


def generate_schedule(
    tasks: List[Task],
    events: List[Event],
    day_start: datetime,
    day_end: datetime,
    buffer_minutes: int = 0,
) -> Tuple[List[ScheduledBlock], List[Task]]:
    scheduled_blocks: List[ScheduledBlock] = []
    unscheduled_tasks: List[Task] = []
    active_block = None

    task_map = {t.id: t for t in tasks}
    scheduled_task_ids: Set[int] = set()
    scheduled_blocks_map: Dict[int, ScheduledBlock] = {}
    remaining_tasks = tasks.copy()

    today_date = day_start.date()

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
        remaining_tasks = [t for t in remaining_tasks if t.id != active_task.id]
        scheduled_task_ids.add(active_task.id)
        scheduled_blocks_map[active_task.id] = active_block

    # Initial free interval
    free_intervals: List[FreeInverval] = [(day_start, day_end)]

    buffer = timedelta(minutes=buffer_minutes)

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

    # Filter eligible tasks
    remaining_tasks = [
        t
        for t in remaining_tasks
        if not t.is_completed
        and (t.scheduled_date is None or t.scheduled_date <= today_date)
    ]
    while remaining_tasks:
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

        if not eligible_tasks:
            unscheduled_tasks.extend(remaining_tasks)
            break

        sorted_tasks = sorted(
            eligible_tasks,
            key=lambda t: (
                t.flexible,
                t.priority,
                t.latest_end_time or datetime.min.time(),
                -t.duration_minutes,
            ),
        )

        task = sorted_tasks[0]
        duration = timedelta(minutes=task.duration_minutes)
        placed = False

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
                task_placable = True
                if buffer > timedelta(0):
                    for block in scheduled_blocks:
                        if (
                            block.start_time < end_time + buffer
                            and block.end_time > end_time
                        ):
                            task_placable = False

                if not task_placable:
                    continue

                placed_block = ScheduledBlock(
                    id=task.id,
                    title=task.title,
                    start_time=start_time,
                    end_time=end_time,
                )
                scheduled_blocks.append(placed_block)
                scheduled_task_ids.add(task.id)
                scheduled_blocks_map[task.id] = placed_block
                remaining_tasks.remove(task)

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

                placed = True
                break

        if not placed:
            unscheduled_tasks.append(task)
            remaining_tasks.remove(task)

    # Sort scheduled blocks by start time
    scheduled_blocks.sort(key=lambda block: block.start_time)

    return scheduled_blocks, unscheduled_tasks
