"""
brain.py — Main processing brain for Folter Assistant.

Every user message is routed here.  The brain uses a simple state-machine
to handle multi-step conversations (e.g., collecting all fields needed to
send an email before actually sending it).

Public API
----------
result = Brain.process(text, session)

  text    : str  — raw user input
  session : dict — mutable state dict (pass {} for a new conversation,
                   keep passing the SAME dict across turns)

Returns BrainResult (namedtuple):
  .message       str   — text to display / speak
  .needs_input   bool  — True  → brain is waiting for a follow-up answer
  .input_hint    str   — placeholder text for the input box while waiting
  .done          bool  — True  → this query is fully complete, session reset
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import os, sys

# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'face-recognition'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hand-guesture'))


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class BrainResult:
    message:     str
    needs_input: bool = False
    input_hint:  str  = "Type your answer…"
    done:        bool = True


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_session() -> dict:
    return {"intent": None, "step": 0, "data": {}}


def _contains(text: str, *words) -> bool:
    return any(w in text for w in words)


# ---------------------------------------------------------------------------
# Individual skill handlers
# Each handler receives:
#   user_input : str   — current user message (already lowercased)
#   session    : dict  — mutable state
# Returns BrainResult
# ---------------------------------------------------------------------------

# ── NEWS ────────────────────────────────────────────────────────────────────

def _handle_news(user_input: str, session: dict) -> BrainResult:
    try:
        from folter_assistant.news import latest_news
        articles = latest_news(max_items=5)
        if isinstance(articles, list) and articles:
            lines = [f"  {i+1}. {a.get('title','')}" for i, a in enumerate(articles)]
            msg = "Latest Headlines:\n" + "\n".join(lines)
        else:
            msg = str(articles)
    except Exception as e:
        msg = f"Could not fetch news: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── WEATHER ─────────────────────────────────────────────────────────────────

def _handle_weather(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)

    if step == 0:
        # Try to extract city from the current message
        city = None
        for prep in ["in ", "at ", "for "]:
            if prep in user_input:
                city = user_input.split(prep, 1)[-1].strip().title()
                break
        if city:
            session["data"]["city"] = city
            session["step"] = 2          # skip asking
        else:
            session["step"] = 1
            return BrainResult(
                message="Which city would you like the weather for?",
                needs_input=True,
                input_hint="Enter city name…",
                done=False,
            )

    if session["step"] == 1:
        session["data"]["city"] = user_input.strip().title() or "Hyderabad"
        session["step"] = 2

    city = session["data"].get("city", "Hyderabad")
    try:
        from folter_assistant.weather import get_weather
        w = get_weather(city)
        msg = (
            f"Weather — {w.get('location','')}, {w.get('region','')}, {w.get('country','')}\n"
            f"  Condition   : {w.get('condition','')}\n"
            f"  Temperature : {w.get('temperature_c','?')}°C  (feels like {w.get('feels_like_c','?')}°C)\n"
            f"  Humidity    : {w.get('humidity','?')}%\n"
            f"  Wind        : {w.get('wind_kph','?')} km/h"
        )
    except Exception as e:
        msg = f"Could not fetch weather: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── WIKIPEDIA ────────────────────────────────────────────────────────────────

def _handle_wikipedia(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)

    if step == 0:
        topic = user_input
        for pfx in ["search for", "search", "wikipedia", "wiki",
                    "what is", "who is", "tell me about"]:
            topic = topic.replace(pfx, "").strip()
        if topic:
            session["data"]["topic"] = topic
            session["step"] = 2
        else:
            session["step"] = 1
            return BrainResult(
                message="What topic would you like me to search on Wikipedia?",
                needs_input=True,
                input_hint="Enter topic…",
                done=False,
            )

    if session["step"] == 1:
        session["data"]["topic"] = user_input.strip()
        session["step"] = 2

    topic = session["data"].get("topic", "")
    try:
        from folter_assistant.wikipedia import search_wikipedia
        result = str(search_wikipedia(topic))
        msg = result[:700] + ("…" if len(result) > 700 else "")
    except Exception as e:
        msg = f"Wikipedia search failed: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── EMAIL ────────────────────────────────────────────────────────────────────

_EMAIL_FIELDS = [
    ("to",       "Recipient email address?",           "recipient@example.com"),
    ("subject",  "Email subject?",                     "Enter subject…"),
    ("body",     "Email body? (type your message)",    "Enter message…"),
    ("sender",   "Your (sender) email address?",       "sender@gmail.com"),
    ("password", "Your email password / app password?","App password…"),
]

def _handle_email(user_input: str, session: dict) -> BrainResult:
    step  = session.get("step", 0)
    data  = session.setdefault("data", {})
    keys  = [f[0] for f in _EMAIL_FIELDS]

    # step 0 → just announce we're collecting
    if step == 0:
        session["step"] = 1
        key, prompt, hint = _EMAIL_FIELDS[0]
        return BrainResult(
            message=f"Sure! Let's compose an email.\n{prompt}",
            needs_input=True,
            input_hint=hint,
            done=False,
        )

    # steps 1‥len(fields) → collect each field
    field_idx = step - 1
    if field_idx < len(_EMAIL_FIELDS):
        key = _EMAIL_FIELDS[field_idx][0]
        data[key] = user_input.strip()

    next_idx = step   # after storing, next field index = step
    if next_idx < len(_EMAIL_FIELDS):
        _, prompt, hint = _EMAIL_FIELDS[next_idx]
        session["step"] = step + 1
        return BrainResult(
            message=prompt,
            needs_input=True,
            input_hint=hint,
            done=False,
        )

    # All fields collected → send
    try:
        from folter_assistant.email import send_email
        send_email(
            smtp_server   = "smtp.gmail.com",
            smtp_port     = 587,
            sender_email  = data["sender"],
            password      = data["password"],
            recipient_email = data["to"],
            subject       = data["subject"],
            body          = data["body"],
        )
        msg = f"✔ Email sent successfully to {data['to']}!"
    except Exception as e:
        msg = f"Failed to send email: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── WHATSAPP ─────────────────────────────────────────────────────────────────

_WA_FIELDS = [
    ("phone",   "Recipient phone number? (with country code, e.g. +91XXXXXXXXXX)", "+91…"),
    ("message", "Message to send?",                                                "Type message…"),
]

def _handle_whatsapp(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)
    data = session.setdefault("data", {})

    if step == 0:
        session["step"] = 1
        _, prompt, hint = _WA_FIELDS[0]
        return BrainResult(
            message=f"Sure! Let's send a WhatsApp message.\n{prompt}",
            needs_input=True,
            input_hint=hint,
            done=False,
        )

    field_idx = step - 1
    if field_idx < len(_WA_FIELDS):
        key = _WA_FIELDS[field_idx][0]
        data[key] = user_input.strip()

    next_idx = step
    if next_idx < len(_WA_FIELDS):
        _, prompt, hint = _WA_FIELDS[next_idx]
        session["step"] = step + 1
        return BrainResult(message=prompt, needs_input=True, input_hint=hint, done=False)

    try:
        from folter_assistant.whatsapp import send_whatsapp_message_instant
        result = send_whatsapp_message_instant(data["phone"], data["message"])
        msg = f"✔ WhatsApp message sent to {data['phone']}!"
    except Exception as e:
        msg = f"Failed to send WhatsApp message: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── REMINDER ─────────────────────────────────────────────────────────────────

_REM_FIELDS = [
    ("task", "What should I remind you about?",         "Enter task…"),
    ("time", "At what date/time? (e.g. 2026-04-17 10:00)", "YYYY-MM-DD HH:MM"),
]

def _handle_reminder(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)
    data = session.setdefault("data", {})

    if step == 0:
        # Try to parse "remind me to X at Y"
        q = user_input
        task = None; time_str = None
        if " at " in q:
            parts = q.split(" at ", 1)
            time_str = parts[1].strip()
            task = parts[0].replace("remind me to", "").replace("reminder", "").strip()
        elif " to " in q:
            task = q.split(" to ", 1)[1].strip()

        if task:
            data["task"] = task
            session["step"] = 2 if time_str else 2  # go ask for time
            if time_str:
                data["time"] = time_str
                session["step"] = 10  # skip to save
            else:
                session["step"] = 2
                return BrainResult(
                    message=f"Noted task: '{task}'\nAt what date/time? (e.g. 2026-04-17 10:00)",
                    needs_input=True, input_hint="YYYY-MM-DD HH:MM", done=False,
                )
        else:
            session["step"] = 1
            return BrainResult(
                message="What should I remind you about?",
                needs_input=True, input_hint="Enter task…", done=False,
            )

    if step == 1:
        data["task"] = user_input.strip()
        session["step"] = 2
        return BrainResult(
            message=f"Got it: '{data['task']}'\nAt what date/time? (e.g. 2026-04-17 10:00)",
            needs_input=True, input_hint="YYYY-MM-DD HH:MM", done=False,
        )

    if step == 2:
        data["time"] = user_input.strip()
        session["step"] = 10

    try:
        from folter_assistant.reminder import ReminderManager
        rm = ReminderManager()
        rm.add_reminder(data["task"], data["time"])
        msg = f"✔ Reminder set: '{data['task']}' at {data['time']}"
    except Exception as e:
        msg = f"Could not set reminder: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── ALARM ────────────────────────────────────────────────────────────────────

def _handle_alarm(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)
    data = session.setdefault("data", {})

    if step == 0:
        q = user_input
        time_str = None
        if " at " in q:
            time_str = q.split(" at ", 1)[1].strip()
        if time_str:
            data["time"] = time_str
            session["step"] = 10
        else:
            session["step"] = 1
            return BrainResult(
                message="At what time should I set the alarm? (e.g. 07:30 AM)",
                needs_input=True, input_hint="HH:MM AM/PM", done=False,
            )

    if step == 1:
        data["time"] = user_input.strip()
        session["step"] = 10

    try:
        from folter_assistant.alarm import AlarmManager
        am = AlarmManager()
        am.add_alarm(data["time"])
        msg = f"✔ Alarm set for {data['time']}"
    except Exception as e:
        msg = f"Could not set alarm: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── BIRTHDAY ─────────────────────────────────────────────────────────────────

def _handle_birthday(user_input: str, session: dict) -> BrainResult:
    try:
        from folter_assistant.birthday import BirthdayManager
        bm = BirthdayManager()
        upcoming = bm.get_upcoming_birthdays()
        if upcoming:
            lines = [f"  • {b}" for b in upcoming]
            msg = "Upcoming Birthdays:\n" + "\n".join(lines)
        else:
            msg = "No upcoming birthdays found."
    except Exception as e:
        msg = f"Birthday lookup failed: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── GREET / HELP / BYE ───────────────────────────────────────────────────────

def _handle_greet(user_input: str, session: dict) -> BrainResult:
    session.update(_new_session())
    return BrainResult(
        message=(
            "Hello! I am Folter Assistant.\n"
            "I can help you with:\n"
            "  • news  • weather  • wikipedia  • email\n"
            "  • whatsapp  • reminder  • alarm  • birthday\n"
            "Just tell me what you need!"
        ),
        done=True,
    )

def _handle_help(user_input: str, session: dict) -> BrainResult:
    session.update(_new_session())
    return BrainResult(
        message=(
            "Available commands:\n"
            "  news            — Latest headlines\n"
            "  weather [city]  — Weather info\n"
            "  search <topic>  — Wikipedia search\n"
            "  send email      — Compose & send an email\n"
            "  send whatsapp   — Send a WhatsApp message\n"
            "  remind me       — Set a reminder\n"
            "  set alarm       — Set an alarm\n"
            "  birthdays       — Upcoming birthdays\n"
            "  bye / exit      — Quit the assistant"
        ),
        done=True,
    )

def _handle_bye(user_input: str, session: dict) -> BrainResult:
    session.update(_new_session())
    return BrainResult(message="GOODBYE|Goodbye! Have a great day!", done=True)


# ---------------------------------------------------------------------------
# Intent detection
# ---------------------------------------------------------------------------

_INTENT_MAP = [
    ("email",     ["send email", "email", "mail"]),
    ("whatsapp",  ["whatsapp", "send whatsapp", "send message", "watsapp"]),
    ("weather",   ["weather", "temperature", "forecast", "climate"]),
    ("news",      ["news", "headline", "headlines", "latest news"]),
    ("wikipedia", ["wikipedia", "wiki", "what is", "who is",
                   "tell me about", "search for", "search"]),
    ("reminder",  ["remind", "reminder", "remind me"]),
    ("alarm",     ["alarm", "wake me", "wake up", "set alarm"]),
    ("birthday",  ["birthday", "birthdays"]),
    ("bye",       ["bye", "exit", "quit", "goodbye", "close"]),
    ("help",      ["help", "what can you do", "features", "commands"]),
    ("greet",     ["hello", "hi", "hey", "how are you", "good morning",
                   "good evening", "good afternoon"]),
]

_HANDLERS = {
    "email":     _handle_email,
    "whatsapp":  _handle_whatsapp,
    "weather":   _handle_weather,
    "news":      _handle_news,
    "wikipedia": _handle_wikipedia,
    "reminder":  _handle_reminder,
    "alarm":     _handle_alarm,
    "birthday":  _handle_birthday,
    "bye":       _handle_bye,
    "help":      _handle_help,
    "greet":     _handle_greet,
}

def _detect_intent(text: str) -> str | None:
    t = text.lower().strip()
    for intent, keywords in _INTENT_MAP:
        for kw in keywords:
            if kw in t:
                return intent
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class Brain:
    @staticmethod
    def process(user_input: str, session: dict) -> BrainResult:
        """
        Process a single user turn.

        Pass the SAME session dict every turn for the same conversation.
        The session is automatically reset after a task completes.
        """
        text = user_input.strip()
        if not text:
            return BrainResult(message="Please type something.", done=True)

        current_intent = session.get("intent")

        # If we're mid-task, keep routing to the same handler
        if current_intent and current_intent in _HANDLERS:
            result = _HANDLERS[current_intent](text.lower(), session)
            if result.done:
                session.update(_new_session())
            return result

        # Fresh message — detect intent
        intent = _detect_intent(text)

        if intent is None:
            return BrainResult(
                message=(
                    f'I didn\'t understand "{text}".\n'
                    "Type 'help' to see what I can do."
                ),
                done=True,
            )

        session["intent"] = intent
        session["step"]   = 0
        session["data"]   = {}

        result = _HANDLERS[intent](text.lower(), session)
        if result.done:
            session.update(_new_session())
        return result
