"""
JARVIS Setup Script
Run this first to install all required dependencies.
Compatible with Python 3.10.0
"""

import subprocess
import sys
import platform
import os

PYTHON = sys.executable

def pip_install(*packages):
    subprocess.check_call([PYTHON, "-m", "pip", "install", "--upgrade", *packages])

def main():
    print("=" * 60)
    print("  JARVIS - Dependency Installer")
    print("  Python:", sys.version)
    print("=" * 60)

    print("\n[1/5] Upgrading pip...")
    subprocess.check_call([PYTHON, "-m", "pip", "install", "--upgrade", "pip"])

    print("\n[2/5] Installing core libraries...")
    pip_install(
        "SpeechRecognition==3.10.0",
        "pyttsx3==2.90",
        "requests==2.31.0",
        "wikipedia==1.4.0",
        "psutil==5.9.8",
        "schedule==1.2.1",
        "pywhatkit==5.4",
    )

    print("\n[3/5] Installing PyAudio (microphone support)...")
    system = platform.system()
    if system == "Windows":
        # Use pipwin for easy PyAudio install on Windows
        try:
            pip_install("pipwin")
            subprocess.check_call([PYTHON, "-m", "pipwin", "install", "pyaudio"])
        except Exception:
            print("  pipwin failed. Trying direct wheel...")
            pip_install("pyaudio")
    elif system == "Darwin":
        print("  On macOS, ensure portaudio is installed: brew install portaudio")
        pip_install("pyaudio")
    else:
        print("  On Linux, ensure portaudio is installed:")
        print("  sudo apt-get install portaudio19-dev python3-pyaudio")
        pip_install("pyaudio")

    print("\n[4/5] Installing optional Windows extras...")
    if system == "Windows":
        try:
            pip_install("pywin32")
            print("  pywin32 installed.")
        except Exception:
            print("  pywin32 skipped (not on Windows or already installed).")

    print("\n[5/5] Creating default config file...")
    import json
    from pathlib import Path

    config_file = Path.home() / ".jarvis_config.json"
    if not config_file.exists():
        config = {
            "name": "JARVIS",
            "wake_word": "jarvis",
            "voice_rate": 170,
            "voice_volume": 1.0,
            "email_address": "YOUR_EMAIL@gmail.com",
            "email_password": "YOUR_APP_PASSWORD",
            "email_smtp": "smtp.gmail.com",
            "email_port": 587,
            "weather_api_key": "GET_FROM_openweathermap.org",
            "news_api_key": "GET_FROM_newsapi.org",
            "city": "Mumbai",
            "whatsapp_phone": "+91XXXXXXXXXX",
        }
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
        print(f"  Config saved to: {config_file}")
        print("  ⚠️  IMPORTANT: Edit this file with your API keys before running JARVIS!")
    else:
        print(f"  Config already exists at: {config_file}")

    print("\n" + "=" * 60)
    print("  ✅  Setup complete!")
    print("\n  NEXT STEPS:")
    print(f"  1. Edit config: {Path.home() / '.jarvis_config.json'}")
    print("     - Add your OpenWeatherMap API key (free at openweathermap.org)")
    print("     - Add your NewsAPI key (free at newsapi.org)")
    print("     - Add your Gmail address + App Password for email")
    print("     - Set your city for weather")
    print("\n  2. Run JARVIS:")
    print("     python jarvis.py")
    print("\n  3. Say 'JARVIS' to wake the assistant!")
    print("=" * 60)

if __name__ == "__main__":
    main()
