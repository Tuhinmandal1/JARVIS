import json
import os
import threading
import time
import uuid
from datetime import datetime

from voice.speaker import Speaker

REMINDERS_FILE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "reminders.json")
)

_lock = threading.Lock()
_speaker = None
_checker_started = False


def _load_reminders():
    if not os.path.exists(REMINDERS_FILE):
        return []
    try:
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_reminders(reminders):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2)


def add_reminder(text: str, time_str: str) -> str:
    """
    Add a reminder. JARVIS will speak it aloud when it comes due.

    Args:
        text: What to remind the user about.
        time_str: When to remind, as "HH:MM" (24-hour, today) or
                   "YYYY-MM-DD HH:MM" for a future date.

    Returns:
        Confirmation message.
    """
    time_str = time_str.strip()

    try:
        if len(time_str) <= 5:
            today = datetime.now().strftime("%Y-%m-%d")
            due = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M")
        else:
            due = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return "I couldn't understand that time. Use HH:MM or YYYY-MM-DD HH:MM."

    with _lock:
        reminders = _load_reminders()
        reminder = {
            "id": str(uuid.uuid4())[:8],
            "text": text,
            "due": due.strftime("%Y-%m-%d %H:%M"),
            "done": False,
        }
        reminders.append(reminder)
        _save_reminders(reminders)

    return f"Reminder set for {due.strftime('%b %d, %H:%M')}: {text}"


def list_reminders() -> str:
    """
    List all upcoming reminders that haven't triggered yet.

    Returns:
        A formatted list of reminders, or a message if there are none.
    """
    with _lock:
        reminders = [r for r in _load_reminders() if not r["done"]]

    if not reminders:
        return "You have no upcoming reminders."

    lines = [f"- [{r['id']}] {r['due']}: {r['text']}" for r in reminders]
    return "Upcoming reminders:\n" + "\n".join(lines)


def delete_reminder(reminder_id: str) -> str:
    """
    Delete a reminder by its id.

    Args:
        reminder_id: The short id shown by list_reminders.

    Returns:
        Confirmation or error message.
    """
    reminder_id = reminder_id.strip()

    with _lock:
        reminders = _load_reminders()
        remaining = [r for r in reminders if r["id"] != reminder_id]

        if len(remaining) == len(reminders):
            return f"No reminder found with id {reminder_id}."

        _save_reminders(remaining)

    return f"Reminder {reminder_id} deleted."


def _checker_loop():
    global _speaker
    _speaker = Speaker()

    while True:
        now = datetime.now()

        with _lock:
            reminders = _load_reminders()
            changed = False

            for r in reminders:
                if r["done"]:
                    continue

                due = datetime.strptime(r["due"], "%Y-%m-%d %H:%M")

                if now >= due:
                    _speaker.speak(f"Reminder: {r['text']}")
                    r["done"] = True
                    changed = True

            if changed:
                _save_reminders(reminders)

        time.sleep(20)


def start_reminder_checker():
    """
    Start the background thread that watches for due reminders and
    speaks them aloud via the Speaker. Safe to call multiple times;
    only actually starts once per process.
    """
    global _checker_started

    if _checker_started:
        return

    _checker_started = True

    thread = threading.Thread(target=_checker_loop, daemon=True)
    thread.start()
