import datetime
import time
import threading
import winsound
from .storage import load_json, save_json


class AlarmManager:
    FILE_NAME = "alarms.json"

    def __init__(self):
        self.alarms = load_json(self.FILE_NAME, default=[])
        self._thread = None
        self._stop_event = threading.Event()

    def _save(self):
        save_json(self.FILE_NAME, self.alarms)

    def set_alarm(self, time_text, label="Alarm"):
        alarm_time = self._parse_time(time_text)
        alarm = {
            "id": int(datetime.datetime.now().timestamp() * 1000),
            "time": alarm_time.isoformat(),
            "label": label,
            "triggered": False,
        }
        self.alarms.append(alarm)
        self._save()
        return alarm

    def list_alarms(self, include_triggered=False):
        return [a for a in self.alarms if include_triggered or not a.get("triggered")]

    def remove_alarm(self, alarm_id):
        self.alarms = [a for a in self.alarms if a.get("id") != alarm_id]
        self._save()

    def _parse_time(self, value):
        if isinstance(value, datetime.datetime):
            return value
        text = str(value).strip()
        formats = ["%H:%M", "%H:%M:%S", "%Y-%m-%d %H:%M", "%d-%m-%Y %H:%M"]
        for fmt in formats:
            try:
                parsed = datetime.datetime.strptime(text, fmt)
                if fmt in ("%H:%M", "%H:%M:%S"):
                    now = datetime.datetime.now()
                    parsed = parsed.replace(year=now.year, month=now.month, day=now.day)
                return parsed
            except ValueError:
                continue
        raise ValueError(f"Could not parse alarm time: {value}")

    def due_alarms(self):
        now = datetime.datetime.now()
        due = []
        for alarm in self.alarms:
            if alarm.get("triggered"):
                continue
            alarm_time = datetime.datetime.fromisoformat(alarm["time"])
            if alarm_time <= now:
                due.append(alarm)
        return due

    def trigger_alarm(self, alarm):
        alarm["triggered"] = True
        self._save()
        try:
            winsound.Beep(1000, 700)
        except Exception:
            print("Alarm: ", alarm.get("label", "Alarm"))

    def run_pending_alarms(self, poll_seconds=30):
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll_alarms, args=(poll_seconds,), daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _poll_alarms(self, poll_seconds):
        while not self._stop_event.is_set():
            for alarm in self.due_alarms():
                self.trigger_alarm(alarm)
            time.sleep(poll_seconds)
