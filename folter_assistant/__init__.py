from .news import latest_news
from .weather import get_weather
from .wikipedia import search_wikipedia
from .reminder import ReminderManager
from .alarm import AlarmManager
from .email import send_email
from .whatsapp import send_whatsapp_message, send_whatsapp_message_instant
from .birthday import BirthdayManager
from .misc import NotesManager

__all__ = [
    "latest_news",
    "get_weather",
    "search_wikipedia",
    "ReminderManager",
    "AlarmManager",
    "send_email",
    "send_whatsapp_message",
    "send_whatsapp_message_instant",
    "BirthdayManager",
    "NotesManager",
]

