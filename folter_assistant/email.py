import ssl
import smtplib
from email.message import EmailMessage


def send_email(
    smtp_server,
    smtp_port,
    sender_email,
    password,
    recipient_email,
    subject,
    body,
    html=False,
):
    """Send an email message through SMTP."""
    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    if html:
        message.add_alternative(body, subtype="html")
    else:
        message.set_content(body)

    context = ssl.create_default_context()
    if smtp_port == 465:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(sender_email, password)
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.send_message(message)
    return True
