"""
SMTP Email Dispatcher Module.

Delivers bilingual (Japanese & English) emails via SMTP with TLS encryption.
Constructs multipart/alternative MIME messages with responsive styled HTML cards
and a clean plain-text fallback. Compatible with Python 3.14.2 standard library.
"""

import os
import re
import sys
import html
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional
from dotenv import load_dotenv

# Ensure Unicode (Japanese) prints properly on Windows terminal
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure") and sys.stderr.encoding.lower() != "utf-8":
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

load_dotenv()

# Basic RFC-compliant email validation regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 587


def is_valid_email(email_address: str) -> bool:
    """Validates basic format of an email address."""
    if not email_address or not isinstance(email_address, str):
        return False
    return bool(EMAIL_REGEX.match(email_address.strip()))


def build_email_html(
    japanese_body: str,
    english_body: str,
    subject: str = "",
    japanese_subject: Optional[str] = None,
) -> str:
    """
    Constructs a responsive dual-card HTML email body.
    - Japanese Primary Card: Light Grey (#f8f9fa) background with Rose accent (#d63384).
    - English Reference Card: Warm Amber (#fff3cd) background with Dark Amber accent (#856404).
    - Footer: Minimalist disclaimer that translation was automatically generated.
    All text is safely escaped with html.escape to prevent markup injection.
    """
    escaped_ja = html.escape(japanese_body.strip()).replace("\n", "<br>\n")
    escaped_en = html.escape(english_body.strip()).replace("\n", "<br>\n")
    escaped_subject = html.escape(subject.strip()) if subject else "Bilingual Communication"

    ja_subject_header = ""
    if japanese_subject and japanese_subject.strip():
        sub_text = japanese_subject.strip()
        if not (sub_text.startswith("【") and sub_text.endswith("】")):
            sub_text = f"【{sub_text}】"
        escaped_ja_sub = html.escape(sub_text)
        ja_subject_header = (
            f'\n          <div style="margin-top: 8px; font-size: 14px; font-weight: 600; color: #212529;">'
            f'件名: {escaped_ja_sub}</div>'
        )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escaped_subject}</title>
</head>
<body style="margin: 0; padding: 24px 12px; background-color: #f1f3f5; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Hiragino Sans', 'Meiryo', sans-serif; color: #212529; line-height: 1.7;">
  <div style="max-width: 640px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);">
    
    <!-- Header Banner -->
    <div style="background: linear-gradient(135deg, #1f2937, #374151); padding: 20px 24px; text-align: left;">
      <h1 style="margin: 0; font-size: 18px; color: #ffffff; font-weight: 600; letter-spacing: 0.5px;">
        ✉️ Bilingual Communication / 日英バイリンガル通知
      </h1>
      <p style="margin: 6px 0 0 0; font-size: 13px; color: #9ca3af;">
        Japanese Primary &bull; English Reference
      </p>
    </div>

    <div style="padding: 24px;">
      <!-- Primary Japanese Card (Rose Accent #d63384 on #f8f9fa) -->
      <div style="background-color: #f8f9fa; border: 1px solid #e9ecef; border-left: 5px solid #d63384; border-radius: 6px; padding: 20px; margin-bottom: 24px;">
        <div style="margin-bottom: 12px;">
          <div>
            <span style="display: inline-block; background-color: #d63384; color: #ffffff; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; margin-right: 8px;">
              日本語
            </span>
            <span style="font-size: 15px; color: #212529; font-weight: 600;">
              本文 (Japanese - Primary)
            </span>
          </div>{ja_subject_header}
        </div>
        <div style="font-size: 15px; color: #212529; white-space: normal; word-break: break-word;">
          {escaped_ja}
        </div>
      </div>

      <!-- Reference English Card (Dark Amber Accent #856404 on #fff3cd) -->
      <div style="background-color: #fff3cd; border: 1px solid #ffeeba; border-left: 5px solid #856404; border-radius: 6px; padding: 20px; margin-bottom: 20px;">
        <div style="margin-bottom: 12px;">
          <span style="display: inline-block; background-color: #856404; color: #ffffff; font-size: 11px; font-weight: bold; padding: 3px 8px; border-radius: 4px; text-transform: uppercase; margin-right: 8px;">
            ENGLISH
          </span>
          <span style="font-size: 14px; color: #856404; font-weight: 600;">
            Original Draft (English Reference)
          </span>
        </div>
        <div style="font-size: 14px; color: #495057; white-space: normal; word-break: break-word;">
          {escaped_en}
        </div>
      </div>
    </div>

    <!-- Minimalist Footer -->
    <div style="background-color: #f8f9fa; border-top: 1px solid #e9ecef; padding: 16px 24px; text-align: center;">
      <p style="margin: 0; font-size: 12px; color: #6c757d; line-height: 1.5;">
        🤖 This email was automatically generated and translated.<br>
        本メールはAIおよび自動翻訳システムによって生成・送信されました。
      </p>
    </div>

  </div>
</body>
</html>"""


def build_email_plain_text(
    japanese_body: str,
    english_body: str,
    japanese_subject: Optional[str] = None,
) -> str:
    """Constructs clean plain-text fallback with ASCII dividers."""
    ja_subject_line = ""
    if japanese_subject and japanese_subject.strip():
        sub_text = japanese_subject.strip()
        if not (sub_text.startswith("【") and sub_text.endswith("】")):
            sub_text = f"【{sub_text}】"
        ja_subject_line = f"件名: {sub_text}\n\n"

    return f"""======================================================================
【日本語】本文 (Japanese - Primary)
======================================================================
{ja_subject_line}{japanese_body.strip()}

======================================================================
【English】Original Draft (English Reference)
======================================================================
{english_body.strip()}

----------------------------------------------------------------------
This email was automatically generated and translated.
本メールはAIおよび自動翻訳システムによって生成・送信されました。
======================================================================
"""


def send_email(
    *args: Any,
    recipient_email: Optional[str] = None,
    subject: Optional[str] = None,
    japanese_body: Optional[str] = None,
    english_body: Optional[str] = None,
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None,
    smtp_host: str = DEFAULT_SMTP_HOST,
    smtp_port: int = DEFAULT_SMTP_PORT,
    japanese_subject: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Sends a bilingual email via SMTP (smtp.gmail.com:587 with STARTTLS).

    Supports flexible calling conventions:
    1. send_email(recipient_email, subject, japanese_body, english_body)
    2. send_email(sender_email, sender_password, recipient_email, subject, japanese_body, english_body)
    3. send_email(recipient_email=..., subject=..., japanese_body=..., english_body=..., japanese_subject=...)

    Credentials default to environment variables:
    - GMAIL_ADDRESS or SENDER_EMAIL
    - GMAIL_APP_PASSWORD or SENDER_APP_PASSWORD

    Returns:
        dict: {"success": bool, "message": str}
    """
    # 1. Normalize positional arguments
    if len(args) == 6:
        # Conceptual signature: (sender, password, recipient, subject, ja_body, en_body)
        sender_email = str(args[0])
        sender_password = str(args[1])
        recipient_email = str(args[2])
        subject = str(args[3])
        japanese_body = str(args[4])
        english_body = str(args[5])
    elif len(args) == 4:
        # Standard signature: (recipient, subject, ja_body, en_body)
        recipient_email = str(args[0])
        subject = str(args[1])
        japanese_body = str(args[2])
        english_body = str(args[3])
    elif len(args) == 5:
        # (recipient, subject, ja_body, en_body, sender)
        recipient_email = str(args[0])
        subject = str(args[1])
        japanese_body = str(args[2])
        english_body = str(args[3])
        sender_email = str(args[4])
    elif len(args) > 0:
        return {
            "success": False,
            "message": f"Invalid number of positional arguments ({len(args)}). Expected 4 or 6.",
        }

    # 2. Check keyword aliases
    recipient_email = (
        recipient_email
        or kwargs.get("to")
        or kwargs.get("recipient")
        or kwargs.get("to_email")
    )
    subject = subject or kwargs.get("title") or "Bilingual Notification / 業務連絡"
    japanese_body = (
        japanese_body
        or kwargs.get("japanese")
        or kwargs.get("ja_body")
        or kwargs.get("ja")
        or ""
    )
    english_body = (
        english_body
        or kwargs.get("english")
        or kwargs.get("en_body")
        or kwargs.get("en")
        or ""
    )
    japanese_subject = (
        japanese_subject
        or kwargs.get("japanese_subject")
        or kwargs.get("ja_subject")
    )
    sender_email = (
        sender_email
        or kwargs.get("from_email")
        or kwargs.get("sender")
        or os.getenv("GMAIL_ADDRESS")
        or os.getenv("SENDER_EMAIL")
    )
    sender_password = (
        sender_password
        or kwargs.get("password")
        or kwargs.get("app_password")
        or os.getenv("GMAIL_APP_PASSWORD")
        or os.getenv("SENDER_APP_PASSWORD")
        or os.getenv("GMAIL_PASSWORD")
    )

    # 3. Input validation
    if not recipient_email or not is_valid_email(recipient_email):
        return {
            "success": False,
            "message": f"Invalid recipient email address: '{recipient_email}'.",
        }

    if not sender_email or not is_valid_email(sender_email):
        return {
            "success": False,
            "message": (
                "Sender email address is missing or invalid. "
                "Please configure GMAIL_ADDRESS in .env or pass sender_email."
            ),
        }

    if not sender_password or not sender_password.strip():
        return {
            "success": False,
            "message": (
                "Sender App Password is not configured. "
                "Please set GMAIL_APP_PASSWORD in .env or pass sender_password."
            ),
        }

    # Strip formatting spaces from Google App Passwords (e.g. 'abcd efgh ijkl mnop')
    cleaned_password = sender_password.strip().replace(" ", "")

    # 4. Construct MIME message
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()

        plain_text = build_email_plain_text(
            japanese_body,
            english_body,
            japanese_subject=japanese_subject,
        )
        html_content = build_email_html(
            japanese_body,
            english_body,
            subject=subject,
            japanese_subject=japanese_subject,
        )

        # In multipart/alternative, plain text comes first, HTML second (priority)
        part_plain = MIMEText(plain_text, "plain", "utf-8")
        part_html = MIMEText(html_content, "html", "utf-8")

        msg.attach(part_plain)
        msg.attach(part_html)
    except Exception as exc:
        return {
            "success": False,
            "message": f"Failed to construct MIME email message: {exc}",
        }

    # 5. Connect and send via SMTP with STARTTLS
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, cleaned_password)
            server.send_message(msg)

        return {
            "success": True,
            "message": f"Email successfully delivered to '{recipient_email}'.",
        }

    except smtplib.SMTPAuthenticationError as auth_err:
        return {
            "success": False,
            "message": (
                "SMTP Authentication Failed: Please check your Gmail address and 16-character App Password. "
                "Ensure Google 2-Step Verification is active and you are using a dedicated App Password "
                f"(not your standard account password). Details: {auth_err}"
            ),
        }
    except smtplib.SMTPException as smtp_err:
        return {
            "success": False,
            "message": f"SMTP delivery error occurred: {smtp_err}",
        }
    except Exception as exc:
        return {
            "success": False,
            "message": f"Unexpected error during email transmission: {exc}",
        }


if __name__ == "__main__":
    print("Testing email_sender.py template rendering...")
    sample_ja = "クライアント各位\nプロジェクトが無事に完了しましたことをご報告申し上げます。"
    sample_en = "Dear Client,\nWe are pleased to inform you that the project has been successfully completed."
    sample_subj = "【プロジェクト完了のご報告】 Project Completion Notification"
    sample_ja_subj = "プロジェクト完了のご報告"

    html_out = build_email_html(
        sample_ja,
        sample_en,
        subject=sample_subj,
        japanese_subject=sample_ja_subj,
    )
    plain_out = build_email_plain_text(
        sample_ja,
        sample_en,
        japanese_subject=sample_ja_subj,
    )

    print("\n--- Plain Text Output Snippet ---")
    print(plain_out[:260] + "...\n")
    print("HTML Template size:", len(html_out), "characters")
    print("Email validation test:", is_valid_email("test@example.com"))
