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
import os, sys, subprocess, webbrowser

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


def _open_with_chrome(url: str | None = None) -> bool:
    if url is None:
        url = "https://www.google.com"
    try:
        subprocess.Popen(["chrome", url], shell=False)
        return True
    except Exception:
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False


def _launch_vscode() -> bool:
    candidates = [
        ["code"],
        [os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Microsoft VS Code", "Code.exe")],
        ["C:\\Program Files\\Microsoft VS Code\\Code.exe"],
        ["C:\\Program Files (x86)\\Microsoft VS Code\\Code.exe"],
    ]
    for cmd in candidates:
        if not cmd[0]:
            continue
        try:
            subprocess.Popen(cmd, shell=False)
            return True
        except Exception:
            continue
    return False


def _launch_hand_gesture() -> bool:
    script_path = os.path.join(os.path.dirname(__file__), "hand-guesture", "hand-guesture.py")
    if not os.path.exists(script_path):
        return False
    try:
        subprocess.Popen([sys.executable, script_path], shell=False)
        return True
    except Exception:
        return False


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

        # Detect category from input
        category = "general"
        for cat in ["business", "entertainment", "health", "science", "sports", "technology"]:
            if cat in user_input:
                category = cat
                break

        is_more = any(w in user_input for w in ["more", "next", "again", "show more"])

        if is_more and session.get("intent") == "news":
            category  = session["data"].get("category", category)
            max_items = session["data"].get("max_items", 5) + 5
        else:
            max_items = 5

        session["intent"]            = "news"
        session["data"]["category"]  = category
        session["data"]["max_items"] = max_items

        articles = latest_news(category=category, max_items=max_items)

        if articles:
            new_articles = articles[max_items - 5:]
            lines = [
                f"  {max_items - 5 + i + 1}. {a['title']}"
                for i, a in enumerate(new_articles)
            ]
            header = f"{'More' if is_more else 'Latest'} {category.title()} News:"
            msg = (
                f"{header}\n"
                + "\n".join(lines)
                + "\n\n  💬 Type 'more' for more, or any other command to exit."
            )
        else:
            msg = "No more news articles found."
            session.update(_new_session())
            return BrainResult(message=msg, done=True)

    except Exception as e:
        msg = f"Could not fetch news: {e}"
        session.update(_new_session())
        return BrainResult(message=msg, done=True)

    return BrainResult(message=msg, done=False)

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
        print(f"Fetching weather for {city}...")
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
    ("recipient", "Recipient email address or name?", "recipient@example.com or Alice"),
    ("subject",   "Email subject?",                     "Enter subject…"),
    ("body",      "Email body? (type your message)",    "Enter message…"),
]

def _handle_email(user_input: str, session: dict) -> BrainResult:
    step  = session.get("step", 0)
    data  = session.setdefault("data", {})

    if step == 0:
        session["step"] = 1
        _, prompt, hint = _EMAIL_FIELDS[0]
        return BrainResult(
            message=f"Sure! Let's compose an email.\n{prompt}",
            needs_input=True,
            input_hint=hint,
            done=False,
        )

    field_idx = step - 1
    if field_idx < len(_EMAIL_FIELDS):
        key = _EMAIL_FIELDS[field_idx][0]
        if key == "recipient":
            from folter_assistant.contacts import ContactBook
            contact_book = ContactBook()
            resolved = contact_book.resolve_email(user_input.strip())
            if not resolved:
                return BrainResult(
                    message=(
                        "I could not resolve that recipient. "
                        "Please enter a valid email address or the contact name from contacts.json."
                    ),
                    needs_input=True,
                    input_hint="recipient@example.com or Alice",
                    done=False,
                )
            data["to"] = resolved
        else:
            data[key] = user_input.strip()

    next_idx = step
    if next_idx < len(_EMAIL_FIELDS):
        _, prompt, hint = _EMAIL_FIELDS[next_idx]
        session["step"] = step + 1
        return BrainResult(
            message=prompt,
            needs_input=True,
            input_hint=hint,
            done=False,
        )

    try:
        from folter_assistant.send_email import send_email
        send_email(
            smtp_server      = "smtp.gmail.com",
            smtp_port        = 587,
            recipient_email  = data["to"],
            subject          = data["subject"],
            body             = data["body"],
        )
        msg = f"✔ Email sent successfully to {data['to']}!"
    except Exception as e:
        msg = f"Failed to send email: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── WHATSAPP ─────────────────────────────────────────────────────────────────

_WA_FIELDS = [
    ("recipient", "Recipient phone number or name? (with country code, e.g. +91XXXXXXXXXX)", "+91… or Alice"),
    ("message",   "Message to send?",                                               "Type message…"),
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
        if key == "recipient":
            from folter_assistant.contacts import ContactBook
            contact_book = ContactBook()
            resolved = contact_book.resolve_phone(user_input.strip())
            if not resolved:
                return BrainResult(
                    message=(
                        "I could not resolve that recipient. "
                        "Please enter a valid phone number or the contact name from contacts.json."
                    ),
                    needs_input=True,
                    input_hint="+91XXXXXXXXXX or Alice",
                    done=False,
                )
            data["phone"] = resolved
        else:
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
    ("recurrence", "Recurrence? (none/daily/weekly/monthly)", "none"),
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
        session["step"] = 3
        return BrainResult(
            message=f"Got time: {data['time']}\nRecurrence? (none/daily/weekly/monthly, default none)",
            needs_input=True, input_hint="none/daily/weekly/monthly", done=False,
        )

    if step == 3:
        recurrence = user_input.strip().lower()
        if recurrence not in ["none", "daily", "weekly", "monthly"]:
            recurrence = "none"
        data["recurrence"] = recurrence
        session["step"] = 10

    try:
        from folter_assistant.reminder import ReminderManager
        rm = ReminderManager()
        rm.add_reminder(data["task"], data["time"], data.get("recurrence", "none"))
        rec = data.get("recurrence", "none")
        msg = f"✔ Reminder set: '{data['task']}' at {data['time']}" + (f" ({rec})" if rec != "none" else "")
    except Exception as e:
        msg = f"Could not set reminder: {e}"
    session.update(_new_session())
    return BrainResult(message=msg, done=True)


# ── BIRTHDAY ─────────────────────────────────────────────────────────────────

def _handle_birthday(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)
    data = session.setdefault("data", {})
    text = user_input.strip()

    try:
        from folter_assistant.birthday import BirthdayManager
        bm = BirthdayManager()
    except Exception as e:
        session.update(_new_session())
        return BrainResult(message=f"Birthday handler failed: {e}", done=True)

    if step == 0:
        if any(keyword in text for keyword in ["add birthday", "add bithday", "new birthday", "new bithday", "remember birthday", "birthday add", "create birthday"]):
            # Direct parse: "add birthday for John on 2026-05-20"
            # or "add birthday on 17 sep for John"
            name = None
            date_text = None
            if " on " in text and " for " in text:
                try:
                    if text.index(" for ") < text.index(" on "):
                        name = text.split(" for ", 1)[1].split(" on ", 1)[0].strip()
                        date_text = text.split(" on ", 1)[1].strip()
                    else:
                        date_text = text.split(" on ", 1)[1].split(" for ", 1)[0].strip()
                        name = text.split(" for ", 1)[1].strip()
                except Exception:
                    name = None
                    date_text = None
            if name and date_text:
                try:
                    bm.add_birthday(name, date_text, note="")
                    session.update(_new_session())
                    return BrainResult(message=f"✔ Birthday saved for {name} on {date_text}", done=True)
                except Exception as e:
                    session.update(_new_session())
                    return BrainResult(message=f"Could not save birthday: {e}", done=True)

            session["step"] = 1
            return BrainResult(
                message="Who is the birthday for?",
                needs_input=True,
                input_hint="Name…",
                done=False,
            )

        # Default birthday query: list upcoming birthdays
        upcoming = bm.upcoming_birthdays()
        if upcoming:
            lines = [f"  • {b['name']} — in {b['in_days']} days ({b['date']})" for b in upcoming]
            msg = "Upcoming Birthdays:\n" + "\n".join(lines)
        else:
            msg = "No upcoming birthdays found."
        session.update(_new_session())
        return BrainResult(message=msg, done=True)

    if step == 1:
        data["name"] = text.strip().title()
        session["step"] = 2
        return BrainResult(
            message="What is the birthday date? (YYYY-MM-DD or DD/MM/YYYY)",
            needs_input=True,
            input_hint="Date…",
            done=False,
        )

    if step == 2:
        data["date"] = text.strip()
        session["step"] = 3
        return BrainResult(
            message="Any note or reminder for this birthday? (optional, type skip to omit)",
            needs_input=True,
            input_hint="Note or skip…",
            done=False,
        )

    if step == 3:
        note_text = text.strip()
        if note_text.lower() in ["skip", "none", ""]:
            note_text = ""
        try:
            bm.add_birthday(data["name"], data["date"], note=note_text)
            msg = f"✔ Birthday saved for {data['name']} on {data['date']}"
        except Exception as e:
            msg = f"Could not save birthday: {e}"
        session.update(_new_session())
        return BrainResult(message=msg, done=True)

    session.update(_new_session())
    return BrainResult(message="No birthday action recognised.", done=True)


# ── GREET / HELP / BYE ───────────────────────────────────────────────────────

def _handle_greet(user_input: str, session: dict) -> BrainResult:
    session.update(_new_session())
    return BrainResult(
        message=(
            "Hello! I am Optima Assistant.\n"
            "I can help you with:\n"
            "  • news  • weather  • wikipedia  • email\n"
            "  • whatsapp  • reminder  • birthdays\n"
            "  • add birthday  • open hand gesture  • recommend\n"
            "Just tell me what you need!"
        ),
        done=True,
    )

def _handle_help(user_input: str, session: dict) -> BrainResult:
    session.update(_new_session())
    return BrainResult(
        message=(
            "Available commands:\n"
            "  news                — Latest headlines\n"
            "  weather [city]      — Weather info\n"
            "  search <topic>      — Wikipedia search\n"
            "  send email          — Compose & send an email\n"
            "  send whatsapp       — Send a WhatsApp message\n"
            "  remind me           — Set a reminder\n"
            "  birthdays           — Show upcoming birthdays\n"
            "  add birthday        — Save a new birthday\n"
            "  open hand gesture   — Launch the hand gesture module\n"
            "  recommend           — Get a recommendation\n"
            "  set profile         — Update preferences or profile info\n"
            "  help                — Show this help list\n"
            "  bye / exit          — Quit the assistant"
        ),
        done=True,
    )

def _handle_open(user_input: str, session: dict) -> BrainResult:
    text = user_input.lower()

    if any(phrase in text for phrase in ["hand gesture", "hand guesture", "gesture"]):
        if _launch_hand_gesture():
            session.update(_new_session())
            return BrainResult(message="✔ Launching hand gesture module...", done=True)
        return BrainResult(message="Could not launch the hand gesture module.", done=True)

    if "youtube" in text:
        ok = _open_with_chrome("https://www.youtube.com")
        return BrainResult(message="✔ Opening YouTube in browser." if ok else "Could not open YouTube.", done=True)

    if "instagram" in text:
        ok = _open_with_chrome("https://www.instagram.com")
        return BrainResult(message="✔ Opening Instagram in browser." if ok else "Could not open Instagram.", done=True)

    if any(term in text for term in ["chrome", "browser"]):
        ok = _open_with_chrome()
        return BrainResult(message="✔ Opening Chrome browser." if ok else "Could not open Chrome.", done=True)

    if any(term in text for term in ["vs code", "vscode", "visual studio code"]):
        ok = _launch_vscode()
        return BrainResult(message="✔ Opening VS Code." if ok else "Could not open VS Code.", done=True)

    if "notepad" in text:
        try:
            subprocess.Popen(["notepad"], shell=False)
            return BrainResult(message="✔ Opening Notepad.", done=True)
        except Exception as e:
            return BrainResult(message=f"Could not open Notepad: {e}", done=True)

    if "control panel" in text:
        try:
            subprocess.Popen(["control"], shell=False)
            return BrainResult(message="✔ Opening Control Panel.", done=True)
        except Exception as e:
            return BrainResult(message=f"Could not open Control Panel: {e}", done=True)

    if "settings" in text:
        try:
            os.startfile("ms-settings:")
            return BrainResult(message="✔ Opening Windows Settings.", done=True)
        except Exception as e:
            return BrainResult(message=f"Could not open Settings: {e}", done=True)

    if "environment" in text or "env" in text or "environment variable" in text:
        try:
            subprocess.Popen(["rundll32.exe", "sysdm.cpl,EditEnvironmentVariables"], shell=False)
            return BrainResult(message="✔ Opening Environment Variables.", done=True)
        except Exception as e:
            return BrainResult(message=f"Could not open Environment Variables: {e}", done=True)

    session.update(_new_session())
    return BrainResult(
        message=(
            "I can open hand gesture, Chrome, VS Code, Notepad, Control Panel, "
            "Settings, Environment Variables, YouTube, or Instagram."
        ),
        done=True,
    )


def _handle_bye(user_input: str, session: dict) -> BrainResult:
    session.update(_new_session())
    return BrainResult(message="GOODBYE|Goodbye! Have a great day!", done=True)

# ── RECOMMEND ────────────────────────────────────────────────────────────────

def _handle_recommend(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)
    data = session.setdefault("data", {})

    # ── Step 0: detect sub-type ──
    if step == 0:
        if any(w in user_input for w in ["movie", "show", "film", "watch"]):
            data["rec_type"] = "movies"
        elif any(w in user_input for w in ["music", "song", "artist", "listen"]):
            data["rec_type"] = "music"
        elif any(w in user_input for w in ["book", "read", "author", "novel"]):
            data["rec_type"] = "books"
        elif any(w in user_input for w in ["youtube", "video", "yt"]):
            data["rec_type"] = "youtube"
        else:
            session["step"] = 1
            return BrainResult(
                message="What would you like recommendations for?\n"
                        "  1. Movies / Shows\n  2. Music\n  3. Books\n  4. YouTube Videos",
                needs_input=True, input_hint="Type movies / music / books / youtube",
                done=False,
            )
        session["step"] = 2

    # ── Step 1: user chose type ──
    if step == 1:
        t = user_input.strip().lower()
        if   "1" in t or "movie" in t or "show" in t:  data["rec_type"] = "movies"
        elif "2" in t or "music" in t or "song" in t:  data["rec_type"] = "music"
        elif "3" in t or "book"  in t or "read" in t:  data["rec_type"] = "books"
        elif "4" in t or "you"   in t or "yt"   in t:  data["rec_type"] = "youtube"
        else:
            return BrainResult(
                message="Please choose: movies / music / books / youtube",
                needs_input=True, input_hint="Type your choice…", done=False,
            )
        session["step"] = 2

    # ── Step 2: ask for keyword/genre (optional) ──
    if step == 2:
        rec_type = data.get("rec_type", "movies")
        hints = {
            "movies":  "Enter genre (action/comedy/drama…) or leave blank",
            "music":   "Enter artist name or genre, or leave blank",
            "books":   "Enter topic or author, or leave blank",
            "youtube": "Enter topic or leave blank",
        }
        session["step"] = 3
        return BrainResult(
            message=f"Got it! Any preference for {rec_type}? (or press Enter to skip)",
            needs_input=True, input_hint=hints.get(rec_type, "Enter preference…"),
            done=False,
        )

    # ── Step 3: fetch recommendations ──
    if step == 3:
        from folter_assistant.recommender import (
            recommend_movies, recommend_music,
            recommend_books, recommend_youtube, log_history,
        )
        rec_type  = data.get("rec_type", "movies")
        preference = user_input.strip() if user_input.strip() not in ["", "skip", "no"] else None

        try:
            if rec_type == "movies":
                items = recommend_movies(genre=preference, max_items=5)
                lines = [
                    f"  {i+1}. {r['title']} ({r['year']}) ⭐{r['rating']}\n"
                    f"     {r['overview']}"
                    for i, r in enumerate(items)
                ]
                header = "🎬 Movie Recommendations:"

            elif rec_type == "music":
                items = recommend_music(artist=preference, max_items=5)
                lines = [
                    f"  {i+1}. {r['track']} — {r['artist']}\n     Album: {r['album']}"
                    for i, r in enumerate(items)
                ]
                header = "🎵 Music Recommendations:"

            elif rec_type == "books":
                items = recommend_books(topic=preference, max_items=5)
                lines = [
                    f"  {i+1}. {r['title']} by {r['author']} ({r['year']})"
                    for i, r in enumerate(items)
                ]
                header = "📚 Book Recommendations:"

            elif rec_type == "youtube":
                items = recommend_youtube(topic=preference, max_items=5)
                lines = [
                    f"  {i+1}. {r['title']}\n     {r['channel']}  →  {r['url']}"
                    for i, r in enumerate(items)
                ]
                header = "▶ YouTube Recommendations:"

            # Log to history
            for item in items:
                log_history(rec_type, item["title"],
                            keywords=[preference] if preference else [])

            msg = (
                f"{header}\n" + "\n".join(lines) +
                f"\n\n  💬 Type 'rate {rec_type}' to rate these, or 'more {rec_type}' for more."
            )

        except Exception as e:
            msg = f"Could not fetch recommendations: {e}"

        data["last_items"] = items if "items" in dir() else []
        data["last_type"]  = rec_type
        session["step"]    = 4
        return BrainResult(message=msg, needs_input=False, done=False)

    # ── Step 4: post-recommendation (rate / more / exit) ──
    if step == 4:
        t = user_input.strip().lower()

        if any(w in t for w in ["rate", "rating"]):
            session["step"] = 5
            return BrainResult(
                message='Which item number would you like to rate? (e.g. "2")',
                needs_input=True, input_hint="Enter item number…", done=False,
            )
        elif any(w in t for w in ["more", "next"]):
            session["step"] = 2   # go back to fetch more
            data["preference"] = data.get("preference")
            return _handle_recommend(t, session)
        else:
            session.update(_new_session())
            return BrainResult(message="Okay! Let me know if you need anything else.", done=True)

    # ── Step 5: collect item number to rate ──
    if step == 5:
        try:
            idx = int(user_input.strip()) - 1
            items = data.get("last_items", [])
            if 0 <= idx < len(items):
                data["rate_item"] = items[idx]["title"]
                session["step"]   = 6
                return BrainResult(
                    message=f'Rate "{data["rate_item"]}" from 1 to 5:',
                    needs_input=True, input_hint="Enter 1-5…", done=False,
                )
        except ValueError:
            pass
        return BrainResult(
            message="Please enter a valid item number.",
            needs_input=True, input_hint="Enter number…", done=False,
        )

    # ── Step 6: save rating ──
    if step == 6:
        try:
            from folter_assistant.recommender import rate_item
            rating = int(user_input.strip())
            rate_item(data["last_type"], data["rate_item"], rating)
            msg = f"✔ Rated '{data['rate_item']}' {rating}/5 — I'll use this to improve recommendations!"
        except Exception as e:
            msg = f"Could not save rating: {e}"
        session.update(_new_session())
        return BrainResult(message=msg, done=True)

    session.update(_new_session())
    return BrainResult(message="Something went wrong. Please try again.", done=True)


# ── PROFILE SETUP ────────────────────────────────────────────────────────────

def _handle_profile(user_input: str, session: dict) -> BrainResult:
    step = session.get("step", 0)
    data = session.setdefault("data", {})

    if step == 0:
        session["step"] = 1
        return BrainResult(
            message="Let's set up your preference profile!\n"
                    "What are your favorite movie genres?\n"
                    "(e.g. action, comedy, thriller, romance — comma separated)",
            needs_input=True, input_hint="action, comedy…", done=False,
        )
    if step == 1:
        from folter_assistant.recommender import set_profile
        genres = [g.strip() for g in user_input.split(",") if g.strip()]
        set_profile("favorite_genres", genres)
        session["step"] = 2
        return BrainResult(
            message=f"✔ Saved genres: {', '.join(genres)}\n"
                    "Your favorite music artists? (comma separated, or skip)",
            needs_input=True, input_hint="Artist1, Artist2… or skip", done=False,
        )
    if step == 2:
        if user_input.strip().lower() not in ["skip", ""]:
            from folter_assistant.recommender import set_profile
            artists = [a.strip() for a in user_input.split(",") if a.strip()]
            set_profile("favorite_artists", artists)
        session["step"] = 3
        return BrainResult(
            message="✔ Saved!\nFavorite book authors? (comma separated, or skip)",
            needs_input=True, input_hint="Author1, Author2… or skip", done=False,
        )
    if step == 3:
        if user_input.strip().lower() not in ["skip", ""]:
            from folter_assistant.recommender import set_profile
            authors = [a.strip() for a in user_input.split(",") if a.strip()]
            set_profile("favorite_authors", authors)
        session.update(_new_session())
        return BrainResult(
            message="✔ Profile saved! I'll use these to personalize your recommendations.\n"
                    "Type 'recommend' anytime to get suggestions!",
            done=True,
        )

    session.update(_new_session())
    return BrainResult(message="Profile setup complete!", done=True)

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
    ("birthday",  ["birthday", "birthdays", "bithday", "bithdays", "add birthday", "add bithday", "new birthday", "new bithday"]),
    ("open",      ["open hand gesture", "hand gesture", "open hand guesture", "hand guesture", "gesture", "open chrome", "open vs code", "open vscode", "open notepad", "open control panel", "open settings", "open environment", "open environment variable", "open youtube", "open instagram"]),
    ("bye",       ["bye", "exit", "quit", "goodbye", "close"]),
    ("help",      ["help", "what can you do", "features", "commands"]),
    ("greet",     ["hello", "hi", "hey", "how are you", "good morning",
                   "good evening", "good afternoon"]),
    ("recommend", ["recommend", "suggest", "recommendation",
                    "what to watch", "what to read", "what to listen",
                    "movie recommendation", "book recommendation",
                    "music recommendation", "youtube recommendation"]),
    ("profile",   ["set profile", "my profile", "preferences",
                   "set preferences", "setup profile"])
]

_HANDLERS = {
    "email":     _handle_email,
    "whatsapp":  _handle_whatsapp,
    "weather":   _handle_weather,
    "news":      _handle_news,
    "wikipedia": _handle_wikipedia,
    "reminder":  _handle_reminder,
    "birthday":  _handle_birthday,
    "open":      _handle_open,
    "bye":       _handle_bye,
    "help":      _handle_help,
    "greet":     _handle_greet,
    "recommend": _handle_recommend,
    "profile":   _handle_profile,
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
        text = user_input.strip()
        if not text:
            return BrainResult(message="Please type something.", done=True)

        t = text.lower()
        current_intent = session.get("intent")
        is_more = any(w in t for w in ["more", "next", "show more"])

        # If mid-news session, only stay if user says "more"
        # Otherwise, detect a new intent first
        if current_intent == "news":
            if is_more:
                return _HANDLERS["news"](t, session)
            else:
                # Check if user wants something else
                new_intent = _detect_intent(text)
                if new_intent and new_intent != "news":
                    # Switch to new intent, clear news session
                    session.update(_new_session())
                    session["intent"] = new_intent
                    session["step"]   = 0
                    session["data"]   = {}
                    result = _HANDLERS[new_intent](t, session)
                    if result.done:
                        session.update(_new_session())
                    return result
                elif new_intent == "news":
                    # Fresh news request
                    session.update(_new_session())
                    session["intent"] = "news"
                    session["step"]   = 0
                    session["data"]   = {}
                    return _HANDLERS["news"](t, session)
                else:
                    # Unrecognized while in news → exit news session
                    session.update(_new_session())
                    return BrainResult(
                        message=f'I didn\'t understand "{text}".\nType \'help\' to see what I can do.',
                        done=True,
                    )

        # If mid-task (non-news), keep routing to same handler
        if current_intent and current_intent in _HANDLERS:
            result = _HANDLERS[current_intent](t, session)
            if result.done:
                session.update(_new_session())
            return result

        # Fresh message — detect intent
        intent = _detect_intent(text)
        if intent is None:
            return BrainResult(
                message=f'I didn\'t understand "{text}".\nType \'help\' to see what I can do.',
                done=True,
            )

        session["intent"] = intent
        session["step"]   = 0
        session["data"]   = {}

        result = _HANDLERS[intent](t, session)
        if result.done:
            session.update(_new_session())
        return result