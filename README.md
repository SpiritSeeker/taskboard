# TaskBoard

TaskBoard is a CLI-based intelligent daily scheduler that converts tasks into a realistic execution plan for the day while respecting calendar events, buffers, and task constraints.

It is designed to reduce cognitive overload by automatically generating a structured daily schedule from a simple task list.

---

## ✨ Current Features

- ✅ Priority-based task scheduling
- ✅ Time window constraints (earliest start / latest end)
- ✅ Buffer between tasks
- ✅ Future task scheduling (scheduled_date support)
- ✅ Active task tracking (start/stop with session logging)
- ✅ Event blocks (manual events that block time)
- ✅ Event-aware scheduling
- ✅ Overlap-safe scheduling engine
- ✅ JSON-based persistence
- ✅ Unit-tested scheduling core

---

## 🧠 Philosophy

TaskBoard is built around a simple idea:

> You should not manually drag tasks around a calendar.
> Your day should be compiled automatically.

The system separates:
- **Tasks** (things you choose to do)
- **Events** (fixed time blocks like meetings or classes)

Tasks are placed around events using a deterministic scheduling engine.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/SpiritSeeker/taskboard.git
cd taskboard
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 📌 Basic Usage

### Add a task

```bash
python -m taskboard.cli.add_task
```

### Start a task

```bash
python -m taskboard.cli.start_task
```

### Stop a task

```bash
python -m taskboard.cli.stop_task
```

### Add an event

```bash
python -m taskboard.cli.add_event
```

### Generate today's schedule

```bash
python -m taskboard.cli.run_today --buffer 15
```

You can customize:
- `--buffer` → transition time between blocks
- Day start/end (via CLI args)

---

## 🗂 Data Storage

- Tasks → `taskboard/storage/tasks.json`
- Events → `taskboard/storage/events.json`

These files are local and not committed to the repository.

---

## 🧪 Running Tests

```bash
pytest
```

The scheduling engine is covered by unit tests to ensure:
- No overlapping blocks
- Buffer correctness
- Event blocking correctness
- Window constraint enforcement

---

## 🔮 Planned Features

- Google / Outlook Calendar sync
- Deadline-aware priority boosting
- Adaptive scheduling based on actual durations
- Multi-day planning
- Web interface

---

## 💬 Feedback Wanted

This project is in active development.

Feedback is especially welcome on:
- Does the generated schedule feel realistic?
- Is the buffer behavior intuitive?
- Does active task handling make sense?
- What feels awkward in the CLI workflow?

Open an issue or share suggestions.
