"""
JARVIS - Personal Desktop Assistant
Python 3.10.0 Compatible
"""

import os
import sys
import threading
import queue
import time
import datetime
import json
import subprocess
import webbrowser
import platform
import re
import smtplib
import glob
import sqlite3
import signal
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

# ─── Dependency check ───────────────────────────────────────────────────────
def check_and_install(packages):
    import importlib, subprocess
    for pkg, import_name in packages:
        try:
            importlib.import_module(import_name)
        except ImportError:
            print(f"Installing {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

REQUIRED = [
    ("SpeechRecognition", "speech_recognition"),
    ("pyttsx3", "pyttsx3"),
    ("requests", "requests"),
    ("wikipedia", "wikipedia"),
    ("playsound", "playsound"),
    ("psutil", "psutil"),
    ("pyaudio", "pyaudio"),
    ("pywhatkit", "pywhatkit"),
    ("schedule", "schedule"),
    ("pywin32", "win32api") if platform.system() == "Windows" else ("", ""),
]

# Filter empty
REQUIRED = [(p, i) for p, i in REQUIRED if p]
check_and_install(REQUIRED)

# ─── Imports after install ───────────────────────────────────────────────────
import speech_recognition as sr
import pyttsx3
import requests
import wikipedia
import psutil
import schedule

# ─── Config ──────────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".jarvis_config.json"
DB_FILE     = Path.home() / ".jarvis_data.db"

DEFAULT_CONFIG = {
    "name": "JARVIS",
    "wake_word": "jarvis",
    "voice_rate": 170,
    "voice_volume": 1.0,
    "email_address": "",
    "email_password": "",
    "email_smtp": "smtp.gmail.com",
    "email_port": 587,
    "weather_api_key": "",          # openweathermap key
    "news_api_key": "",             # newsapi.org key
    "city": "Mumbai",
    "whatsapp_phone": "",
}

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            cfg = json.load(f)
        # Merge missing keys
        for k, v in DEFAULT_CONFIG.items():
            cfg.setdefault(k, v)
        return cfg
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

CONFIG = load_config()

# ─── Database ────────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        remind_at TEXT,
        done INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        created_at TEXT,
        done INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()

init_db()

# ─── TTS Engine ──────────────────────────────────────────────────────────────
class Speaker:
    def __init__(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", CONFIG["voice_rate"])
        self.engine.setProperty("volume", CONFIG["voice_volume"])
        self._set_voice()
        self._stop_flag = threading.Event()
        self._lock = threading.Lock()

    def _set_voice(self):
        voices = self.engine.getProperty("voices")
        # Prefer a female / natural-sounding voice
        for v in voices:
            if "zira" in v.name.lower() or "female" in v.name.lower() or "hazel" in v.name.lower():
                self.engine.setProperty("voice", v.id)
                return
        if voices:
            self.engine.setProperty("voice", voices[0].id)

    def speak(self, text: str):
        """Speak text; can be interrupted by calling stop()."""
        self._stop_flag.clear()
        print(f"\n[JARVIS]: {text}\n")
        # Split into sentences for interruptible speech
        sentences = re.split(r'(?<=[.!?]) +', text)
        for sentence in sentences:
            if self._stop_flag.is_set():
                break
            with self._lock:
                try:
                    self.engine.say(sentence)
                    self.engine.runAndWait()
                except Exception:
                    pass

    def stop(self):
        self._stop_flag.set()
        try:
            self.engine.stop()
        except Exception:
            pass

SPEAKER = Speaker()

def speak(text):
    SPEAKER.speak(text)

def stop_speaking():
    SPEAKER.stop()

# ─── Speech Recognition ──────────────────────────────────────────────────────
RECOGNIZER = sr.Recognizer()
RECOGNIZER.pause_threshold = 0.8
RECOGNIZER.energy_threshold = 300

def listen(timeout=5, phrase_limit=10) -> str:
    """Listen from mic and return text (lower-case)."""
    with sr.Microphone() as source:
        RECOGNIZER.adjust_for_ambient_noise(source, duration=0.3)
        try:
            audio = RECOGNIZER.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
            text = RECOGNIZER.recognize_google(audio)
            print(f"[YOU]: {text}")
            return text.lower()
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return ""

# ─── Interruptible Listener ───────────────────────────────────────────────────
# While JARVIS speaks, a background thread listens for "stop" or new commands.
INTERRUPT_QUEUE = queue.Queue()

def background_listener():
    """Runs forever; puts detected speech into INTERRUPT_QUEUE."""
    while True:
        try:
            with sr.Microphone() as source:
                RECOGNIZER.adjust_for_ambient_noise(source, duration=0.2)
                audio = RECOGNIZER.listen(source, timeout=3, phrase_time_limit=8)
                text = RECOGNIZER.recognize_google(audio).lower()
                if text:
                    INTERRUPT_QUEUE.put(text)
        except Exception:
            pass

def start_background_listener():
    t = threading.Thread(target=background_listener, daemon=True)
    t.start()

# ─── Reminders ───────────────────────────────────────────────────────────────
def save_reminder(text: str, remind_at: datetime.datetime):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO reminders (text, remind_at) VALUES (?, ?)",
              (text, remind_at.isoformat()))
    conn.commit()
    conn.close()
    # Schedule it
    delay = (remind_at - datetime.datetime.now()).total_seconds()
    if delay > 0:
        threading.Timer(delay, lambda: speak(f"Reminder: {text}")).start()
    speak(f"Reminder set: '{text}' at {remind_at.strftime('%I:%M %p on %B %d')}")

def save_task(text: str):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO tasks (text, created_at) VALUES (?, ?)",
              (text, datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    speak(f"Task saved: {text}")

def list_tasks():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, text FROM tasks WHERE done=0 ORDER BY id DESC LIMIT 10")
    rows = c.fetchall()
    conn.close()
    if not rows:
        speak("You have no pending tasks.")
        return
    msg = f"You have {len(rows)} pending tasks. "
    for i, (tid, text) in enumerate(rows, 1):
        msg += f"{i}. {text}. "
    speak(msg)

def reload_reminders():
    """Reload pending reminders from DB on startup."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT text, remind_at FROM reminders WHERE done=0")
    rows = c.fetchall()
    conn.close()
    now = datetime.datetime.now()
    for text, remind_at_str in rows:
        try:
            remind_at = datetime.datetime.fromisoformat(remind_at_str)
            delay = (remind_at - now).total_seconds()
            if delay > 0:
                threading.Timer(delay, lambda t=text: speak(f"Reminder: {t}")).start()
        except Exception:
            pass

reload_reminders()

# ─── Parse time from command ──────────────────────────────────────────────────
def parse_reminder_time(command: str):
    """Return (text, datetime) or (None, None)."""
    now = datetime.datetime.now()
    # "remind me to X in N minutes/hours/days"
    m = re.search(r"remind(?:\s+me)?\s+(?:to\s+)?(.+?)\s+in\s+(\d+)\s+(minute|hour|day|second)s?", command)
    if m:
        text = m.group(1).strip()
        amount = int(m.group(2))
        unit = m.group(3)
        delta = {"second": datetime.timedelta(seconds=amount),
                 "minute": datetime.timedelta(minutes=amount),
                 "hour":   datetime.timedelta(hours=amount),
                 "day":    datetime.timedelta(days=amount)}[unit]
        return text, now + delta

    # "remind me to X at HH:MM" or "at 3pm"
    m = re.search(r"remind(?:\s+me)?\s+(?:to\s+)?(.+?)\s+at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", command)
    if m:
        text = m.group(1).strip()
        hour = int(m.group(2))
        minute = int(m.group(3)) if m.group(3) else 0
        ampm = m.group(4)
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        remind_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if remind_at < now:
            remind_at += datetime.timedelta(days=1)
        return text, remind_at

    return None, None

# ─── Weather ──────────────────────────────────────────────────────────────────
def get_weather(city=None):
    city = city or CONFIG["city"]
    api_key = CONFIG["weather_api_key"]
    if not api_key:
        speak("Please add your OpenWeatherMap API key to the config file.")
        return
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        r = requests.get(url, timeout=5)
        data = r.json()
        if data.get("cod") != 200:
            speak(f"Could not get weather for {city}.")
            return
        desc  = data["weather"][0]["description"]
        temp  = data["main"]["temp"]
        feels = data["main"]["feels_like"]
        humid = data["main"]["humidity"]
        wind  = data["wind"]["speed"]
        speak(f"Weather in {city}: {desc}. Temperature is {temp:.1f}°C, feels like {feels:.1f}°C. "
              f"Humidity {humid}%, wind speed {wind} m/s.")
    except Exception as e:
        speak(f"Weather service error: {e}")

# ─── News ─────────────────────────────────────────────────────────────────────
NEWS_CACHE = []

def get_news(query=None):
    global NEWS_CACHE
    api_key = CONFIG["news_api_key"]
    if not api_key:
        speak("Please add your NewsAPI key to the config file to get news.")
        return []
    try:
        if query:
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=5&apiKey={api_key}"
        else:
            url = f"https://newsapi.org/v2/top-headlines?country=in&pageSize=10&apiKey={api_key}"
        r = requests.get(url, timeout=5)
        articles = r.json().get("articles", [])
        NEWS_CACHE = articles
        return articles
    except Exception as e:
        speak(f"News service error: {e}")
        return []

def read_news_headlines():
    articles = get_news()
    if not articles:
        return
    speak(f"Here are the top {len(articles)} news headlines.")
    for i, a in enumerate(articles, 1):
        title = a.get("title", "").split(" - ")[0]
        speak(f"{i}. {title}")
        # Check for interruption
        if not INTERRUPT_QUEUE.empty():
            cmd = INTERRUPT_QUEUE.get()
            handle_interrupt(cmd, articles)
            return

def read_news_detail(index_or_keyword):
    """Read full description of a news article."""
    articles = NEWS_CACHE if NEWS_CACHE else get_news()
    target = None
    # Try by number
    try:
        idx = int(index_or_keyword) - 1
        if 0 <= idx < len(articles):
            target = articles[idx]
    except ValueError:
        # Search by keyword
        for a in articles:
            if index_or_keyword in a.get("title", "").lower():
                target = a
                break
    if target:
        title = target.get("title", "")
        desc  = target.get("description", "") or target.get("content", "") or "No details available."
        speak(f"{title}. {desc}")
    else:
        speak("Could not find that article.")

def handle_interrupt(cmd, articles):
    stop_speaking()
    if "stop" in cmd:
        return
    # Try to find article reference
    m = re.search(r"(headline|article|news)\s*(\d+)|tell me more about (.+)", cmd)
    if m:
        ref = m.group(2) or m.group(3)
        read_news_detail(ref)
    else:
        process_command(cmd)

# ─── Wikipedia ───────────────────────────────────────────────────────────────
def search_wikipedia(query: str):
    try:
        wikipedia.set_lang("en")
        result = wikipedia.summary(query, sentences=4)
        speak(result)
    except wikipedia.exceptions.DisambiguationError as e:
        speak(f"Multiple results found. Did you mean: {', '.join(e.options[:3])}?")
    except wikipedia.exceptions.PageError:
        speak(f"No Wikipedia page found for {query}.")
    except Exception as e:
        speak(f"Wikipedia error: {e}")

# ─── Web Search / Open website ───────────────────────────────────────────────
def open_website(url_or_name: str):
    url = url_or_name.strip()
    if not url.startswith("http"):
        # Common shortcuts
        shortcuts = {
            "youtube": "https://youtube.com",
            "gmail":   "https://mail.google.com",
            "google":  "https://google.com",
            "github":  "https://github.com",
            "twitter": "https://twitter.com",
            "x":       "https://x.com",
            "linkedin":"https://linkedin.com",
            "reddit":  "https://reddit.com",
            "maps":    "https://maps.google.com",
            "netflix": "https://netflix.com",
            "amazon":  "https://amazon.in",
            "flipkart":"https://flipkart.com",
        }
        if url in shortcuts:
            url = shortcuts[url]
        else:
            url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
    webbrowser.open(url)
    speak(f"Opening {url_or_name}")

def google_search(query: str):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    speak(f"Searching Google for {query}")

# ─── Email ────────────────────────────────────────────────────────────────────
def send_email(to: str, subject: str, body: str):
    cfg = CONFIG
    if not cfg["email_address"] or not cfg["email_password"]:
        speak("Please configure your email in the config file.")
        return
    try:
        msg = MIMEMultipart()
        msg["From"]    = cfg["email_address"]
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP(cfg["email_smtp"], cfg["email_port"])
        server.starttls()
        server.login(cfg["email_address"], cfg["email_password"])
        server.sendmail(cfg["email_address"], to, msg.as_string())
        server.quit()
        speak(f"Email sent to {to} successfully.")
    except Exception as e:
        speak(f"Failed to send email: {e}")

def compose_email_voice():
    speak("Who should I send the email to?")
    to = listen(timeout=8)
    if not to:
        speak("I didn't catch the recipient.")
        return
    speak("What is the subject?")
    subject = listen(timeout=8)
    speak("What should the email say?")
    body = listen(timeout=15)
    speak(f"Sending email to {to}, subject: {subject}. Body: {body}. Say yes to confirm.")
    confirm = listen(timeout=5)
    if "yes" in confirm:
        send_email(to, subject, body)
    else:
        speak("Email cancelled.")

# ─── WhatsApp ─────────────────────────────────────────────────────────────────
def send_whatsapp(phone: str, message: str, hour: int = None, minute: int = None):
    try:
        import pywhatkit
        now = datetime.datetime.now()
        h = hour if hour is not None else now.hour
        m = minute if minute is not None else now.minute + 2
        if m >= 60:
            m -= 60
            h += 1
        pywhatkit.sendwhatmsg(phone, message, h, m, wait_time=15, tab_close=True)
        speak(f"WhatsApp message scheduled to {phone}.")
    except Exception as e:
        speak(f"WhatsApp error: {e}")

def compose_whatsapp_voice():
    speak("What is the phone number including country code?")
    phone = listen(timeout=8).replace(" ", "")
    if not phone:
        speak("No phone number detected.")
        return
    speak("What message should I send?")
    message = listen(timeout=15)
    speak(f"Sending WhatsApp to {phone}: {message}. Say yes to confirm.")
    confirm = listen(timeout=5)
    if "yes" in confirm:
        send_whatsapp(phone, message)
    else:
        speak("WhatsApp cancelled.")

# ─── File Search ──────────────────────────────────────────────────────────────
def search_files(query: str, path: str = None):
    search_path = path or str(Path.home())
    speak(f"Searching for {query} in {search_path}. This may take a moment.")
    results = []
    pattern = f"**/*{query}*"
    try:
        for p in Path(search_path).rglob(f"*{query}*"):
            results.append(str(p))
            if len(results) >= 10:
                break
    except PermissionError:
        pass
    if results:
        speak(f"Found {len(results)} file(s) matching '{query}'.")
        for i, r in enumerate(results[:5], 1):
            speak(f"{i}. {Path(r).name} in {Path(r).parent}")
    else:
        speak(f"No files found matching '{query}'.")
    return results

# ─── Open Application ─────────────────────────────────────────────────────────
APP_MAP_WINDOWS = {
    "notepad":    "notepad.exe",
    "calculator": "calc.exe",
    "paint":      "mspaint.exe",
    "chrome":     "chrome.exe",
    "firefox":    "firefox.exe",
    "word":       "winword.exe",
    "excel":      "excel.exe",
    "powerpoint": "powerpnt.exe",
    "vlc":        "vlc.exe",
    "spotify":    "spotify.exe",
    "vscode":     "code",
    "cmd":        "cmd.exe",
    "explorer":   "explorer.exe",
    "teams":      "Teams.exe",
    "zoom":       "Zoom.exe",
    "discord":    "Discord.exe",
}

APP_MAP_LINUX = {
    "files":       "nautilus",
    "calculator":  "gnome-calculator",
    "text editor": "gedit",
    "chrome":      "google-chrome",
    "firefox":     "firefox",
    "vscode":      "code",
    "terminal":    "gnome-terminal",
    "vlc":         "vlc",
    "spotify":     "spotify",
}

def open_application(app_name: str):
    system = platform.system()
    try:
        if system == "Windows":
            exe = APP_MAP_WINDOWS.get(app_name.lower(), app_name)
            subprocess.Popen([exe], shell=True)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", app_name])
        else:
            exe = APP_MAP_LINUX.get(app_name.lower(), app_name)
            subprocess.Popen([exe])
        speak(f"Opening {app_name}")
    except Exception as e:
        speak(f"Could not open {app_name}: {e}")

# ─── Alarm ────────────────────────────────────────────────────────────────────
def set_alarm(hour: int, minute: int, label: str = "Alarm"):
    now = datetime.datetime.now()
    alarm_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if alarm_time < now:
        alarm_time += datetime.timedelta(days=1)
    delay = (alarm_time - now).total_seconds()
    threading.Timer(delay, lambda: _trigger_alarm(label)).start()
    speak(f"Alarm set for {alarm_time.strftime('%I:%M %p')}. Label: {label}")

def _trigger_alarm(label: str):
    speak(f"Wake up! {label}! It's time!")
    # Beep 3 times
    for _ in range(3):
        print("\a")
        time.sleep(1)

def parse_alarm_command(command: str):
    """Parse 'set alarm at 7 30 am morning workout'"""
    m = re.search(r"alarm\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?(?:\s+(?:for\s+)?(.+))?", command)
    if m:
        hour   = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm   = m.group(3)
        label  = m.group(4) or "Alarm"
        if ampm == "pm" and hour != 12: hour += 12
        elif ampm == "am" and hour == 12: hour = 0
        set_alarm(hour, minute, label.strip())
        return True
    return False

# ─── System Controls ──────────────────────────────────────────────────────────
def clear_desktop():
    """Close all windows except JARVIS."""
    system = platform.system()
    speak("Closing all applications except myself.")
    try:
        if system == "Windows":
            subprocess.call("taskkill /F /IM chrome.exe /T", shell=True)
            subprocess.call("taskkill /F /IM firefox.exe /T", shell=True)
            subprocess.call("taskkill /F /IM notepad.exe /T", shell=True)
            # More graceful: close all explorer windows
            subprocess.call('powershell "Get-Process | Where-Object {$_.MainWindowTitle -ne \'\'} | Stop-Process"', shell=True)
        elif system == "Darwin":
            subprocess.call("osascript -e 'tell application \"System Events\" to set quitapps to name of every application process whose visible is true' -e 'repeat with appname in quitapps' -e 'tell application appname to quit' -e 'end repeat'", shell=True)
        else:
            subprocess.call("wmctrl -c :ACTIVE:", shell=True)
    except Exception as e:
        speak(f"Error clearing desktop: {e}")

def shutdown_system():
    speak("Shutting down the system in 10 seconds. Say cancel to abort.")
    time.sleep(10)
    system = platform.system()
    if system == "Windows":
        subprocess.call("shutdown /s /t 1", shell=True)
    elif system == "Darwin":
        subprocess.call(["sudo", "shutdown", "-h", "now"])
    else:
        subprocess.call(["sudo", "shutdown", "-h", "now"])

def restart_system():
    speak("Restarting in 10 seconds.")
    time.sleep(10)
    system = platform.system()
    if system == "Windows":
        subprocess.call("shutdown /r /t 1", shell=True)
    elif system == "Darwin":
        subprocess.call(["sudo", "shutdown", "-r", "now"])
    else:
        subprocess.call(["sudo", "reboot"])

# ─── Utility ──────────────────────────────────────────────────────────────────
def tell_time():
    now = datetime.datetime.now()
    speak(f"The current time is {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}.")

def tell_date():
    now = datetime.datetime.now()
    speak(f"Today is {now.strftime('%A, %B %d, %Y')}.")

def tell_about_jarvis():
    speak("""I am JARVIS, your personal desktop assistant. 
I can answer questions, search the web and Wikipedia, 
read you the news, set reminders and alarms, 
send emails and WhatsApp messages, 
search your files, open apps and websites, 
tell you the weather, manage your tasks, 
and control your system. Just say my name to wake me up!""")

def system_info():
    cpu  = psutil.cpu_percent(interval=1)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    speak(f"CPU usage: {cpu}%. RAM used: {ram.percent}%, "
          f"{ram.used // (1024**3)} GB of {ram.total // (1024**3)} GB. "
          f"Disk used: {disk.percent}%.")

def calculate(expression: str):
    try:
        # Safe eval
        allowed = set("0123456789+-*/().% ")
        clean = "".join(c for c in expression if c in allowed)
        result = eval(clean)
        speak(f"The answer is {result}")
    except Exception:
        speak("I couldn't calculate that.")

# ─── Command Router ──────────────────────────────────────────────────────────
def process_command(command: str):
    """Route a voice command to the correct handler."""
    cmd = command.lower().strip()

    # ── Stop ──
    if cmd in ("stop", "stop speaking", "quiet", "shut up", "pause"):
        stop_speaking()
        return

    # ── Time / Date ──
    if any(x in cmd for x in ["what time", "current time", "tell me the time"]):
        tell_time(); return
    if any(x in cmd for x in ["what date", "today's date", "what day"]):
        tell_date(); return

    # ── Weather ──
    if "weather" in cmd:
        m = re.search(r"weather\s+(?:in|of|for)?\s+(.+)", cmd)
        city = m.group(1).strip() if m else None
        get_weather(city); return

    # ── News ──
    if any(x in cmd for x in ["news headline", "top news", "latest news", "news update"]):
        read_news_headlines(); return
    if "news about" in cmd or "headlines about" in cmd:
        m = re.search(r"(?:news|headlines) about (.+)", cmd)
        if m:
            articles = get_news(m.group(1))
            if articles:
                speak(f"Here are results for {m.group(1)}.")
                for i, a in enumerate(articles[:5], 1):
                    speak(f"{i}. {a['title'].split(' - ')[0]}")
        return
    if re.search(r"tell me more about (headline|article|news)?\s*(\d+)", cmd):
        m = re.search(r"(\d+)", cmd)
        if m: read_news_detail(int(m.group(1))); return

    # ── Wikipedia ──
    if any(x in cmd for x in ["wikipedia", "who is", "what is", "tell me about"]):
        query = re.sub(r"(search wikipedia for|wikipedia|who is|what is|tell me about)", "", cmd).strip()
        if query: search_wikipedia(query)
        return

    # ── Google search ──
    if "search" in cmd and "google" in cmd:
        query = re.sub(r"(search google for|google search|search on google)", "", cmd).strip()
        google_search(query); return
    if "search for" in cmd:
        query = cmd.split("search for", 1)[1].strip()
        google_search(query); return

    # ── Open website ──
    if "open" in cmd and any(x in cmd for x in ["youtube", "gmail", "google", "github", "twitter",
                                                   "linkedin", "reddit", "netflix", "amazon", "flipkart",
                                                   "website", "http", ".com", ".in", ".org"]):
        site = re.sub(r"open\s+(website\s+)?", "", cmd).strip()
        open_website(site); return

    # ── Open application ──
    if "open" in cmd:
        app = re.sub(r"open\s+", "", cmd).strip()
        open_application(app); return

    # ── Email ──
    if "send email" in cmd or "compose email" in cmd or "write email" in cmd:
        compose_email_voice(); return

    # ── WhatsApp ──
    if "whatsapp" in cmd or "send message" in cmd or "send whatsapp" in cmd:
        compose_whatsapp_voice(); return

    # ── Alarm ──
    if "alarm" in cmd:
        if not parse_alarm_command(cmd):
            speak("Could not parse alarm time. Please say: set alarm at 7 30 am."); return
        return

    # ── Reminder ──
    if "remind" in cmd:
        text, remind_at = parse_reminder_time(cmd)
        if text and remind_at:
            save_reminder(text, remind_at)
        else:
            speak("I couldn't understand the reminder time. Try: remind me to call mom in 2 hours.")
        return

    # ── Task ──
    if "add task" in cmd or "save task" in cmd or "note" in cmd:
        task_text = re.sub(r"(add task|save task|add a task|make a note|note)", "", cmd).strip()
        save_task(task_text); return
    if "list task" in cmd or "my tasks" in cmd or "show tasks" in cmd or "pending tasks" in cmd:
        list_tasks(); return

    # ── File search ──
    if "find file" in cmd or "search file" in cmd or "locate file" in cmd:
        query = re.sub(r"(find file|search file|locate file|find a file|search for file)", "", cmd).strip()
        search_files(query); return

    # ── System info ──
    if "system info" in cmd or "cpu usage" in cmd or "ram usage" in cmd or "battery" in cmd:
        system_info(); return

    # ── Calculate ──
    if "calculate" in cmd or "what is" in cmd and any(op in cmd for op in ["+", "-", "*", "/", "plus", "minus", "times"]):
        expr = re.sub(r"(calculate|what is|equals)", "", cmd)
        expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*").replace("divided by", "/")
        calculate(expr); return

    # ── Clear desktop ──
    if "clear desktop" in cmd or "close all apps" in cmd or "close all windows" in cmd:
        clear_desktop(); return

    # ── Shutdown ──
    if "shut down" in cmd or "shutdown" in cmd:
        shutdown_system(); return
    if "restart" in cmd or "reboot" in cmd:
        restart_system(); return

    # ── About ──
    if "who are you" in cmd or "what can you do" in cmd or "help" in cmd:
        tell_about_jarvis(); return

    # ── Greetings ──
    if any(x in cmd for x in ["hello", "hi", "hey", "good morning", "good evening", "good afternoon"]):
        hour = datetime.datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 17 else "Good evening"
        speak(f"{greet}! How can I help you?"); return

    # ── Fallback: Wikipedia ──
    if len(cmd) > 3:
        speak(f"Let me look that up for you.")
        search_wikipedia(cmd)
    else:
        speak("I'm not sure how to help with that. Could you rephrase?")

# ─── Main Loop ────────────────────────────────────────────────────────────────
def main():
    wake_word = CONFIG["wake_word"]
    print("=" * 60)
    print(f"  {CONFIG['name']} - Personal Desktop Assistant")
    print(f"  Say '{wake_word.upper()}' to activate")
    print("  Press Ctrl+C to exit")
    print("=" * 60)

    speak(f"Hello! I am {CONFIG['name']}, your personal assistant. Say {wake_word} to activate me.")

    start_background_listener()

    while True:
        try:
            # Check interrupt queue first
            if not INTERRUPT_QUEUE.empty():
                cmd = INTERRUPT_QUEUE.get()
                if wake_word in cmd or "stop" in cmd:
                    stop_speaking()
                    if wake_word in cmd:
                        speak("Yes? How can I help?")
                        command = listen(timeout=7, phrase_limit=15)
                        if command:
                            process_command(command)
                    continue

            # Primary listen for wake word
            text = listen(timeout=3, phrase_limit=5)
            if not text:
                continue

            if wake_word in text:
                stop_speaking()
                speak("Yes?")
                command = listen(timeout=8, phrase_limit=20)
                if command:
                    process_command(command)

        except KeyboardInterrupt:
            speak("Goodbye! Have a great day!")
            sys.exit(0)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(0.5)

if __name__ == "__main__":
    main()
