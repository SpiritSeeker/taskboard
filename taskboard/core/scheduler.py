from datetime import datetime, timedelta
from typing import List, Tuple

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

    today_date = day_start.date()

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

    # Filter incomplete tasks
    tasks = [
        task
        for task in tasks
        if (
            not task.is_completed
            and (task.scheduled_date is None or task.scheduled_date <= today_date)
        )
    ]

    # Sort tasks
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            t.flexible,
            t.priority,
            t.latest_end_time or datetime.min.time(),
            -t.duration_minutes,
        ),
    )

    for task in sorted_tasks:
        duration = timedelta(minutes=task.duration_minutes)
        placed = False

        for i, (free_start, free_end) in enumerate(free_intervals):
            window_start = free_start
            window_end = free_end

            if task.earliest_start_time:
                window_start = max(
                    free_start,
                    datetime.combine(day_start.date(), task.earliest_start_time),
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

                scheduled_blocks.append(
                    ScheduledBlock(
                        id=task.id,
                        title=task.title,
                        start_time=start_time,
                        end_time=end_time,
                    )
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

                placed = True
                break

        if not placed:
            unscheduled_tasks.append(task)

    # Sort scheduled blocks by start time
    scheduled_blocks.sort(key=lambda block: block.start_time)

    return scheduled_blocks, unscheduled_tasks
