import ssl
import requests
# Disable SSL verification globally to handle self-signed certificates in corporate networks
_original_create_default_context = ssl.create_default_context

def _patched_create_default_context(*args, **kwargs):
    ctx = _original_create_default_context(*args, **kwargs)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

ssl.create_default_context = _patched_create_default_context

# Also patch requests to disable SSL verification
_original_request = requests.Session.request
def _patched_request(self, method, url, **kwargs):
    kwargs.setdefault('verify', False)
    return _original_request(self, method, url, **kwargs)
requests.Session.request = _patched_request

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import pywhatkit
import time


def send_whatsapp_message(phone_number, message, wait_seconds=15):
    """
    Send a WhatsApp message from your own number using WhatsApp Web.
    
    Args:
        phone_number: Target phone number (with country code, e.g., "+91XXXXXXXXXX")
        message: Message text to send
        wait_seconds: Time to wait for WhatsApp Web to load (default 15)
    
    Returns:
        dict with status
    """
    if not phone_number or not message:
        raise ValueError("Phone number and message are required.")
    
    try:
        hour = time.localtime().tm_hour
        minute = time.localtime().tm_min + 1
        
        pywhatkit.sendwhatmsg(phone_number, message, hour, minute, wait_time=wait_seconds)
        return {"status": "success", "message": "Message scheduled for sending"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def send_whatsapp_message_instant(phone_number, message):
    """
    Send a WhatsApp message instantly (requires browser to be open with WhatsApp Web).
    
    Args:
        phone_number: Target phone number (with country code, e.g., "+91XXXXXXXXXX")
        message: Message text to send
    
    Returns:
        dict with status
    """
    if not phone_number or not message:
        raise ValueError("Phone number and message are required.")
    
    try:
        pywhatkit.sendwhatmsg_instantly(phone_number, message, wait_time=5)
        return {"status": "success", "message": "Message sent instantly"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
