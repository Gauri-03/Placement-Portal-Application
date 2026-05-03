"""
mailer.py — Email sending utility using smtplib + MailHog (local SMTP).

MailHog runs on SMTP port 1025 (no auth, no TLS).
Web UI: http://localhost:8025
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def send_email(to: str, subject: str, html_body: str, attachments: list = None):
    """
    Send an HTML email via MailHog (local SMTP).

    Args:
        to:          Recipient email address (string or list of strings)
        subject:     Email subject line
        html_body:   HTML content of the email body
        attachments: Optional list of dicts:
                     [{"filename": "export.csv", "data": b"...", "mimetype": "text/csv"}]
    """
    from flask import current_app

    mail_server = current_app.config.get("MAIL_SERVER", "localhost")
    mail_port = current_app.config.get("MAIL_PORT", 1025)
    sender = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@launchpad.com")

    # Support single address or list
    recipients = [to] if isinstance(to, str) else to

    msg = MIMEMultipart("mixed")
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    # Attach HTML body
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach any files
    if attachments:
        for attachment in attachments:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment["data"])
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{attachment["filename"]}"',
            )
            part.add_header("Content-Type", attachment.get("mimetype", "application/octet-stream"))
            msg.attach(part)

    try:
        with smtplib.SMTP(mail_server, mail_port) as server:
            server.sendmail(sender, recipients, msg.as_string())
        print(f"[mailer] Email sent to {recipients}: {subject}")
        return True
    except Exception as e:
        print(f"[mailer] Failed to send email to {recipients}: {e}")
        return False
