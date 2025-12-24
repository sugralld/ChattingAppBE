import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Dict, Any


def send_email(to_email: str, subject: str, body: str, html: Optional[str] = None) -> Dict[str, Any]:
    """
    Send an email using SMTP. Requires SMTP_HOST, SMTP_USER, SMTP_PASS.

    Environment variables:
      - SMTP_HOST
      - SMTP_PORT (default 587)
      - SMTP_USER
      - SMTP_PASS
      - SMTP_USE_SSL (true/false, default false)
      - SMTP_USE_TLS (true/false, default true)
      - EMAIL_FROM (default SMTP_USER or no-reply@chattingapp.local)
      - EMAIL_DEV_MODE (set to "true" to enable dev-mode)

    Returns: {"success": True, "result": {...}} or {"success": False, "error": "..."}
    When EMAIL_DEV_MODE is true and SMTP is not configured, returns {"success": True, "dev": True, "message": ...}
    """
    EMAIL_DEV_MODE = os.getenv("EMAIL_DEV_MODE", "false").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "false").lower() == "true"
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    FROM = os.getenv("EMAIL_FROM", SMTP_USER or "no-reply@chattingapp.local")

    # If SMTP is not configured, fall back to dev-mode if enabled
    if not SMTP_HOST or not SMTP_USER or not SMTP_PASS:
        if EMAIL_DEV_MODE:
            print("[email_utils] DEV MODE - SMTP not configured. Email not sent.")
            print(f"To: {to_email} | Subject: {subject} | Body: {body}")
            return {"success": True, "dev": True, "message": "Dev mode - email not sent"}
        return {"success": False, "error": "SMTP configuration missing. Set SMTP_HOST, SMTP_USER, SMTP_PASS or enable EMAIL_DEV_MODE for testing."}

    # Build message
    msg = EmailMessage()
    msg["From"] = FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")

    try:
        # SSL (implicit) or STARTTLS (explicit)
        if SMTP_USE_SSL:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        else:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            try:
                server.ehlo()
                if SMTP_USE_TLS:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
            finally:
                try:
                    server.quit()
                except Exception:
                    pass

        return {"success": True, "result": {"provider": "smtp"}}
    except Exception as e:
        print(f"[email_utils] SMTP error: {e}")
        return {"success": False, "error": str(e)}
