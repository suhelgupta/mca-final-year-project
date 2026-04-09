import datetime
from .storage import load_json, save_json


class BirthdayManager:
    FILE_NAME = "birthdays.json"

    def __init__(self):
        self.birthdays = load_json(self.FILE_NAME, default=[])

    def _save(self):
        save_json(self.FILE_NAME, self.birthdays)

    def add_birthday(self, name, date_text, note=""):
        birth_date = self._parse_date(date_text)
        birthday = {
            "id": int(datetime.datetime.now().timestamp() * 1000),
            "name": name,
            "date": birth_date.isoformat(),
            "note": note,
        }
        self.birthdays.append(birthday)
        self._save()
        return birthday

    def list_birthdays(self):
        return self.birthdays

    def remove_birthday(self, birthday_id):
        self.birthdays = [b for b in self.birthdays if b.get("id") != birthday_id]
        self._save()

    def today_birthdays(self):
        today = datetime.date.today()
        return [b for b in self.birthdays if datetime.date.fromisoformat(b["date"]).month == today.month and datetime.date.fromisoformat(b["date"]).day == today.day]

    def upcoming_birthdays(self, days=30):
        today = datetime.date.today()
        result = []
        for birthday in self.birthdays:
            date = datetime.date.fromisoformat(birthday["date"])
            candidate = datetime.date(today.year, date.month, date.day)
            if candidate < today:
                candidate = datetime.date(today.year + 1, date.month, date.day)
            delta = (candidate - today).days
            if 0 <= delta <= days:
                result.append({"name": birthday["name"], "in_days": delta, "date": birthday["date"], "note": birthday.get("note", "")})
        return sorted(result, key=lambda item: item["in_days"])

    def _parse_date(self, value):
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            return value
        text = str(value).strip()
        formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %B %Y", "%d %b %Y"]
        for fmt in formats:
            try:
                return datetime.datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Could not parse birthday date: {value}")
