# 🤖 JARVIS — Personal Desktop Assistant

> A fully voice-controlled personal desktop assistant built with Python 3.10.0

---

## ⚡ Quick Start

```bash
# 1. Install dependencies
python setup.py

# 2. Edit your config (see Configuration below)
# Located at: ~/.jarvis_config.json

# 3. Run JARVIS
python jarvis.py
```

Say **"JARVIS"** to wake the assistant, then speak your command.

---

## 🛠️ Features

| Feature | Voice Command Examples |
|---|---|
| **Wake word** | *"JARVIS"* |
| **Interrupt / Stop** | *"Stop"* (any time while speaking) |
| **Time & Date** | *"JARVIS, what time is it?"* |
| **Weather** | *"JARVIS, what's the weather in Delhi?"* |
| **Top News** | *"JARVIS, give me the news headlines"* |
| **News Detail** | *"Tell me more about headline 3"* |
| **Wikipedia** | *"JARVIS, who is Elon Musk?"* / *"What is quantum computing?"* |
| **Google Search** | *"JARVIS, search Google for best Python tutorials"* |
| **Open Website** | *"JARVIS, open YouTube"* / *"Open GitHub"* |
| **Open App** | *"JARVIS, open Notepad"* / *"Open Chrome"* |
| **Send Email** | *"JARVIS, send an email"* (guided voice flow) |
| **WhatsApp** | *"JARVIS, send WhatsApp message"* (guided voice flow) |
| **Reminder** | *"JARVIS, remind me to drink water in 30 minutes"* |
| **Reminder (time)** | *"JARVIS, remind me to call mom at 6 pm"* |
| **Task / Note** | *"JARVIS, add task buy groceries"* |
| **List Tasks** | *"JARVIS, show my tasks"* |
| **Set Alarm** | *"JARVIS, set alarm at 7 30 am morning workout"* |
| **File Search** | *"JARVIS, find file project report"* |
| **System Info** | *"JARVIS, CPU usage"* |
| **Calculate** | *"JARVIS, calculate 245 times 18"* |
| **Clear Desktop** | *"JARVIS, close all apps"* |
| **Shutdown** | *"JARVIS, shut down the system"* |
| **Restart** | *"JARVIS, restart the computer"* |
| **About** | *"JARVIS, what can you do?"* |

---

## 🔑 Configuration (`~/.jarvis_config.json`)

```json
{
  "name": "JARVIS",
  "wake_word": "jarvis",
  "voice_rate": 170,
  "voice_volume": 1.0,
  "email_address": "you@gmail.com",
  "email_password": "your_gmail_app_password",
  "email_smtp": "smtp.gmail.com",
  "email_port": 587,
  "weather_api_key": "your_openweathermap_key",
  "news_api_key": "your_newsapi_key",
  "city": "Mumbai",
  "whatsapp_phone": "+91XXXXXXXXXX"
}
```

### Getting Free API Keys

| Service | URL | Usage |
|---|---|---|
| **Weather** | https://openweathermap.org/api | Free tier — 1000 calls/day |
| **News** | https://newsapi.org | Free tier — 100 calls/day |

### Gmail App Password
1. Enable 2-Factor Authentication on your Google account
2. Go to: Google Account → Security → App Passwords
3. Create a new app password → copy it into `email_password`
> ⚠️ Never use your actual Gmail password

---

## 📦 Dependencies

```
SpeechRecognition==3.10.0   # Voice-to-text
pyttsx3==2.90               # Text-to-speech (offline)
requests==2.31.0            # HTTP / API calls
wikipedia==1.4.0            # Wikipedia search
psutil==5.9.8               # System monitoring
schedule==1.2.1             # Task scheduling
pywhatkit==5.4              # WhatsApp messaging
pyaudio                     # Microphone input
pywin32                     # Windows system control (Windows only)
```

---

## 🎤 How Interruption Works

JARVIS runs a **background listener thread** at all times.  
While JARVIS is speaking:
- Say **"stop"** → JARVIS stops immediately
- Say **"JARVIS, [new command]"** → stops current speech, starts new task
- Say **"tell me more about headline 3"** → during news reading, switches to that article

---

## ⏰ Reminders & Alarms

Reminders are stored in an SQLite database (`~/.jarvis_data.db`) and survive restarts.

```
"Remind me to take medicine in 2 hours"
"Remind me to call the bank at 3 pm"
"Set alarm at 6 30 am gym"
```

---

## 📱 WhatsApp

Uses `pywhatkit`, which opens WhatsApp Web in your browser and auto-sends.  
Your PC must be logged into WhatsApp Web.

---

## 🔍 File Search

Recursively searches your home directory for files matching the keyword.

```
"Find file invoice"
"Search file resume"
"Locate file project notes"
```

---

## 🌐 Websites JARVIS Knows By Name

`youtube`, `gmail`, `google`, `github`, `twitter`, `x`, `linkedin`,
`reddit`, `maps`, `netflix`, `amazon`, `flipkart`

For anything else, say the full domain: *"Open stackoverflow.com"*

---

## 🖥️ Applications JARVIS Can Open (Windows)

`notepad`, `calculator`, `paint`, `chrome`, `firefox`, `word`,
`excel`, `powerpoint`, `vlc`, `spotify`, `vscode`, `cmd`, `explorer`,
`teams`, `zoom`, `discord`

---

## 💡 Tips

- Speak clearly and at normal pace
- Pause briefly after saying "JARVIS" before your command
- For email/WhatsApp, JARVIS will guide you step by step
- Background noise reduces accuracy — use in a quieter environment
- Increase `voice_rate` in config for faster speech (default: 170 wpm)

---

## 🐍 Python Version

Tested and compatible with **Python 3.10.0**

---

*Built with ❤️ — Your personal AI assistant*
