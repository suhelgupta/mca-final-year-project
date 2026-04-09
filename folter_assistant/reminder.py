import datetime
from .storage import load_json, save_json


class ReminderManager:
    FILE_NAME = "reminders.json"

    def __init__(self):
        self.reminders = load_json(self.FILE_NAME, default=[])

    def _save(self):
        save_json(self.FILE_NAME, self.reminders)

    def add_reminder(self, text, remind_at):
        remind_at = self._parse_datetime(remind_at)
        reminder = {
            "id": int(datetime.datetime.now().timestamp() * 1000),
            "text": text,
            "remind_at": remind_at.isoformat(),
            "done": False,
        }
        self.reminders.append(reminder)
        self._save()
        return reminder

    def list_reminders(self, include_done=False):
        return [r for r in self.reminders if include_done or not r.get("done")]

    def remove_reminder(self, reminder_id):
        self.reminders = [r for r in self.reminders if r.get("id") != reminder_id]
        self._save()

    def mark_done(self, reminder_id):
        for reminder in self.reminders:
            if reminder.get("id") == reminder_id:
                reminder["done"] = True
                self._save()
                return reminder
        return None

    def due_reminders(self):
        now = datetime.datetime.now()
        due = []
        for reminder in self.reminders:
            if reminder.get("done"):
                continue
            remind_at = datetime.datetime.fromisoformat(reminder["remind_at"])
            if remind_at <= now:
                due.append(reminder)
        return due

    def _parse_datetime(self, value):
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day, 9, 0)

        text = str(value).strip()
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d-%m-%Y %H:%M",
            "%d-%m-%Y",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%H:%M",
        ]
        for fmt in formats:
            try:
                parsed = datetime.datetime.strptime(text, fmt)
                if fmt == "%H:%M":
                    now = datetime.datetime.now()
                    parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
                return parsed
            except ValueError:
                continue
        raise ValueError(f"Could not parse reminder time: {value}")
