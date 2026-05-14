import re
from .storage import load_json

FILE_NAME = "contacts.json"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(value: str) -> bool:
    if not value:
        return False
    return bool(_EMAIL_RE.fullmatch(value.strip()))


def normalize_phone(value: str) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"[^\d+]+", "", value.strip())
    if cleaned.startswith("+") and len(cleaned) >= 8:
        return cleaned
    if cleaned.isdigit() and len(cleaned) >= 8:
        return cleaned
    return None


class ContactBook:
    def __init__(self):
        self.contacts = load_json(FILE_NAME, default=[])

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower()

    def find_by_name(self, name: str) -> dict | None:
        normalized = self._normalize_name(name)
        if not normalized:
            return None

        exact_matches = [
            contact for contact in self.contacts
            if self._normalize_name(contact.get("name", "")) == normalized
        ]
        if exact_matches:
            return exact_matches[0]

        partial_matches = [
            contact for contact in self.contacts
            if normalized in self._normalize_name(contact.get("name", ""))
        ]
        if len(partial_matches) == 1:
            return partial_matches[0]

        return None

    def resolve_email(self, value: str) -> str | None:
        if not value:
            return None
        value = value.strip()
        if is_valid_email(value):
            return value
        contact = self.find_by_name(value)
        if contact:
            email = contact.get("email")
            return email.strip() if email else None
        return None

    def resolve_phone(self, value: str) -> str | None:
        if not value:
            return None
        value = value.strip()
        phone = normalize_phone(value)
        if phone:
            return phone
        contact = self.find_by_name(value)
        if contact:
            return normalize_phone(contact.get("phone", ""))
        return None
