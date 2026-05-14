import ssl
import smtplib
from email.message import EmailMessage


def send_email(
    smtp_server,
    smtp_port,
    recipient_email,
    subject,
    body,
    html=False,
):
    login_email = "suhel.gupta.01@gmail.com"
    login_password = "boptooxkawuujnye"

    message = EmailMessage()
    message["From"] = login_email
    message["To"] = recipient_email
    message["Subject"] = subject

    if html:
        message.add_alternative(body, subtype="html")
    else:
        message.set_content(body)

    context = ssl.create_default_context()

    if smtp_port == 465:
        with smtplib.SMTP_SSL(
            smtp_server,
            smtp_port,
            context=context
        ) as server:
            server.login(login_email, login_password)
            server.send_message(message)
    else:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(login_email, login_password)
            server.send_message(message)

    return True


if __name__ == "__main__":
    print("Sending test email...")
    send_email(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        recipient_email="suhelgupta1792@gmail.com",
        subject="Test Email",
        body="This is a test email sent from Python."
    )