import sys
import os
import importlib

# Add folders with hyphens to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'face-recognition'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hand-guesture'))

# Import from face-recognition folder
from check_user import check_user

# Import from Helpers package
# from Helpers import listen, speak

# Import from folter_assistant package
from folter_assistant import (
    latest_news,
    get_weather,
    search_wikipedia,
    ReminderManager,
    AlarmManager,
    send_email,
    send_whatsapp_message_instant,
    BirthdayManager,
)


def main():
    """Main application entry point with face recognition and assistant features."""
    print("Checking user authentication...")
    if check_user(True):
        print("User recognized. Access granted.")
        print("Welcome to Folter Assistant!")
        print("\nAvailable features:")
        print("1. News - Get latest headlines")
        print("2. Weather - Check weather details")
        print("3. Wikipedia - Search for information")
        print("4. Reminders - Set persistent reminders")
        print("5. Alarms - Schedule alarms")
        print("6. Email - Send emails")
        print("7. WhatsApp - Send WhatsApp messages")
        print("8. Birthdays - Track birthdays")
        print("\nAdd your main application code here!")
    else:
        print("User not recognized. Access denied.")
        exit(1)


if __name__ == "__main__":
    main()

