"""
Test Dispatcher Module.

Provides sandbox / dry-run email dispatching capabilities via disposable
Ethereal email accounts (powered by Nodemailer Ethereal API).

Features:
1. Dynamic disposable account creation via Ethereal API.
2. Automated test run: generates temporary sender & recipient, builds bilingual
   multipart MIME email, transmits via Ethereal SMTP, and captures web preview URL.
3. Manual test run: allows arbitrary custom sender & recipient addresses (provider-agnostic),
   routes via provisioned Ethereal relay, and provides a web preview URL.

Compatible with Python 3.14.2 standard library.
"""

import os
import re
import sys
import json
import time
import smtplib
import email.utils
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

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

# Ensure project root is available in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from email_trans.email_sender import build_email_html, build_email_plain_text, is_valid_email

ETHEREAL_API_URL = "https://api.nodemailer.com/user"
ETHEREAL_DEFAULT_HOST = "smtp.ethereal.email"
ETHEREAL_DEFAULT_PORT = 587


class EtherealSMTP(smtplib.SMTP):
    """
    Custom SMTP client that intercepts the DATA response from Ethereal SMTP.
    Ethereal includes '[STATUS=new MSGID=...]' in the 250 DATA completion reply,
    which allows direct construction of the public message preview URL.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.last_data_response: Optional[bytes] = None

    def data(self, msg: Any) -> tuple[int, bytes]:
        code, resp = super().data(msg)
        self.last_data_response = resp
        return code, resp


def create_ethereal_account(retries: int = 2, timeout: int = 15) -> dict[str, Any]:
    """
    Creates a disposable test email account via the Nodemailer Ethereal API.

    API Endpoint: POST https://api.nodemailer.com/user
    Payload: {'requestor': 'email_translator', 'version': '1.0.0'}

    Returns:
        dict: Account metadata including 'user', 'pass', 'smtp', 'web', etc.

    Raises:
        RuntimeError: If account creation fails after specified retries.
    """
    payload = json.dumps({"requestor": "email_translator", "version": "1.0.0"}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "email_translator/1.0.0",
    }

    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(ETHEREAL_API_URL, data=payload, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status not in (200, 201):
                    raise RuntimeError(f"Ethereal API returned HTTP {response.status}")
                raw_body = response.read().decode("utf-8")
                account_data = json.loads(raw_body)
                if not account_data.get("user") or not account_data.get("pass"):
                    raise ValueError(f"Incomplete account credentials in response: {raw_body}")
                return account_data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.0)

    raise RuntimeError(
        f"Failed to provision disposable Ethereal account after {retries + 1} attempts: {last_error}"
    ) from last_error


def _extract_msgid_from_smtp_response(response_bytes: Optional[bytes]) -> Optional[str]:
    """Extracts the unique MSGID string from Ethereal's 250 DATA response."""
    if not response_bytes:
        return None
    text = response_bytes.decode("utf-8", errors="ignore")
    match = re.search(r"MSGID=([^\s\]]+)", text)
    return match.group(1) if match else None


def _format_subject(subject: Optional[str], japanese_subject: Optional[str] = None) -> str:
    """Combines Japanese subject and English subject into the standard formatted subject line."""
    clean_subj = (subject or "").strip()
    clean_ja = (japanese_subject or "").strip()

    if clean_ja:
        bracketed_ja = clean_ja if (clean_ja.startswith("【") and clean_ja.endswith("】")) else f"【{clean_ja}】"
        if clean_subj:
            if bracketed_ja in clean_subj:
                return clean_subj
            return f"{bracketed_ja} {clean_subj}"
        return bracketed_ja

    return clean_subj or "Bilingual Test Run / 業務連絡"


def send_automatic_test_run(
    japanese_body: str,
    english_body: str,
    subject: str = "Bilingual Test Run / 業務連絡",
    japanese_subject: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Executes a fully automated dry-run test using two temporary disposable Ethereal accounts.

    1. Provisions temp_sender and temp_recip via Ethereal API.
    2. Constructs bilingual MIME multipart email with HTML and plain-text fallback.
    3. Connects to Ethereal SMTP with STARTTLS and dispatches email.
    4. Extracts the message preview URL.

    Args:
        japanese_body: Japanese content for the primary card.
        english_body: English content for the reference card.
        subject: Subject line for the email.
        japanese_subject: Optional dedicated Japanese subject line.

    Returns:
        dict: {
            'success': bool,
            'mode': 'automatic',
            'sender': str,
            'recipient': str,
            'subject': str,
            'smtp_host': str,
            'smtp_port': int,
            'preview_url': str,
            'message': str,
        }
    """
    final_subject = _format_subject(subject, japanese_subject)

    # 1. Input validation
    if not japanese_body or not str(japanese_body).strip():
        return {
            "success": False,
            "mode": "automatic",
            "error": "Japanese body cannot be empty.",
            "message": "Automated test run failed: Japanese body cannot be empty.",
        }

    if not english_body or not str(english_body).strip():
        return {
            "success": False,
            "mode": "automatic",
            "error": "English body cannot be empty.",
            "message": "Automated test run failed: English body cannot be empty.",
        }

    # 2. Provision temporary accounts
    try:
        temp_sender = create_ethereal_account()
        temp_recip = create_ethereal_account()
    except Exception as exc:
        return {
            "success": False,
            "mode": "automatic",
            "error": str(exc),
            "message": f"Failed to provision temporary test accounts: {exc}",
        }

    sender_email = temp_sender["user"]
    sender_pass = temp_sender["pass"]
    recipient_email = temp_recip["user"]

    smtp_cfg = temp_sender.get("smtp", {})
    smtp_host = smtp_cfg.get("host") or ETHEREAL_DEFAULT_HOST
    smtp_port = int(smtp_cfg.get("port") or ETHEREAL_DEFAULT_PORT)

    # 3. Construct MIME multipart email
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = final_subject
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()

        plain_text = build_email_plain_text(
            japanese_body=japanese_body,
            english_body=english_body,
            japanese_subject=japanese_subject,
        )
        html_content = build_email_html(
            japanese_body=japanese_body,
            english_body=english_body,
            subject=final_subject,
            japanese_subject=japanese_subject,
        )

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))
    except Exception as exc:
        return {
            "success": False,
            "mode": "automatic",
            "sender": sender_email,
            "recipient": recipient_email,
            "subject": final_subject,
            "error": str(exc),
            "message": f"Failed to construct MIME email message: {exc}",
        }

    # 4. Connect, authenticate, and dispatch via Ethereal SMTP
    try:
        with EtherealSMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_pass)
            server.send_message(msg)
            data_resp = server.last_data_response

        msg_id = _extract_msgid_from_smtp_response(data_resp)
        preview_url = (
            f"https://ethereal.email/message/{msg_id}"
            if msg_id
            else f"https://ethereal.email/login (User: {temp_recip['user']})"
        )

        return {
            "success": True,
            "mode": "automatic",
            "sender": sender_email,
            "recipient": recipient_email,
            "subject": final_subject,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "preview_url": preview_url,
            "message": "Automated dry-run completed successfully!",
        }

    except smtplib.SMTPAuthenticationError as auth_err:
        return {
            "success": False,
            "mode": "automatic",
            "sender": sender_email,
            "recipient": recipient_email,
            "subject": final_subject,
            "error": str(auth_err),
            "message": f"SMTP Authentication failed with temporary test account: {auth_err}",
        }
    except (smtplib.SMTPException, OSError) as smtp_err:
        return {
            "success": False,
            "mode": "automatic",
            "sender": sender_email,
            "recipient": recipient_email,
            "subject": final_subject,
            "error": str(smtp_err),
            "message": f"SMTP delivery error to test relay: {smtp_err}",
        }
    except Exception as exc:
        return {
            "success": False,
            "mode": "automatic",
            "sender": sender_email,
            "recipient": recipient_email,
            "subject": final_subject,
            "error": str(exc),
            "message": f"Unexpected error during automated test run: {exc}",
        }


def send_manual_test_run(
    sender_email: str,
    recipient_email: str,
    japanese_body: str,
    english_body: str,
    subject: str = "Bilingual Test Run / 業務連絡",
    japanese_subject: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Executes a provider-agnostic test run using a provisioned test SMTP relay.

    Allows any arbitrary sender email address (does not require Gmail or an app password)
    and any recipient email address. The transmission is securely routed through a
    temporary Ethereal SMTP credential with STARTTLS, preserving the custom From
    and To headers, and returning the online web preview link.

    Args:
        sender_email: Any custom sender email address.
        recipient_email: Any destination recipient email address.
        japanese_body: Japanese content for the primary card.
        english_body: English content for the reference card.
        subject: Subject line for the email.
        japanese_subject: Optional dedicated Japanese subject line.

    Returns:
        dict: {
            'success': bool,
            'mode': 'manual',
            'delivery_status': 'delivered' | 'failed',
            'status': 'delivered' | 'failed',
            'sender': str,
            'recipient': str,
            'subject': str,
            'smtp_host': str,
            'smtp_port': int,
            'preview_url': str,
            'message': str,
        }
    """
    final_subject = _format_subject(subject, japanese_subject)
    norm_sender = (sender_email or "").strip()
    norm_recipient = (recipient_email or "").strip()

    # 1. Address format validation
    if not norm_sender or not is_valid_email(norm_sender):
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": f"Invalid sender email address: '{norm_sender}'",
            "message": f"Invalid sender email address: '{norm_sender}'.",
        }

    if not norm_recipient or not is_valid_email(norm_recipient):
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": f"Invalid recipient email address: '{norm_recipient}'",
            "message": f"Invalid recipient email address: '{norm_recipient}'.",
        }

    if not japanese_body or not str(japanese_body).strip():
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": "Japanese body cannot be empty.",
            "message": "Manual test run failed: Japanese body cannot be empty.",
        }

    if not english_body or not str(english_body).strip():
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": "English body cannot be empty.",
            "message": "Manual test run failed: English body cannot be empty.",
        }

    # 2. Provision temporary relay credentials
    try:
        relay_account = create_ethereal_account()
    except Exception as exc:
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": str(exc),
            "message": f"Failed to provision test SMTP relay: {exc}",
        }

    smtp_cfg = relay_account.get("smtp", {})
    smtp_host = smtp_cfg.get("host") or ETHEREAL_DEFAULT_HOST
    smtp_port = int(smtp_cfg.get("port") or ETHEREAL_DEFAULT_PORT)
    relay_user = relay_account["user"]
    relay_pass = relay_account["pass"]

    # 3. Construct bilingual MIME multipart message with custom From and To
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = final_subject
        msg["From"] = norm_sender
        msg["To"] = norm_recipient
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()

        plain_text = build_email_plain_text(
            japanese_body=japanese_body,
            english_body=english_body,
            japanese_subject=japanese_subject,
        )
        html_content = build_email_html(
            japanese_body=japanese_body,
            english_body=english_body,
            subject=final_subject,
            japanese_subject=japanese_subject,
        )

        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))
    except Exception as exc:
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": str(exc),
            "message": f"Failed to construct MIME email message: {exc}",
        }

    # 4. Dispatch via SMTP STARTTLS using test relay credentials
    try:
        with EtherealSMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(relay_user, relay_pass)

            # Attempt dispatch with custom From; fallback to envelope sender if server restricts
            try:
                server.send_message(msg)
            except smtplib.SMTPSenderRefused:
                server.send_message(msg, from_addr=relay_user)

            data_resp = server.last_data_response

        msg_id = _extract_msgid_from_smtp_response(data_resp)
        preview_url = (
            f"https://ethereal.email/message/{msg_id}"
            if msg_id
            else f"https://ethereal.email/login (Relay User: {relay_user})"
        )

        return {
            "success": True,
            "mode": "manual",
            "status": "delivered",
            "delivery_status": "delivered",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "relay_account": relay_user,
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "preview_url": preview_url,
            "message": f"Manual test run successfully dispatched to '{norm_recipient}'.",
        }

    except smtplib.SMTPAuthenticationError as auth_err:
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": str(auth_err),
            "message": f"Test SMTP relay authentication failed: {auth_err}",
        }
    except (smtplib.SMTPException, OSError) as smtp_err:
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": str(smtp_err),
            "message": f"SMTP delivery error through test relay: {smtp_err}",
        }
    except Exception as exc:
        return {
            "success": False,
            "mode": "manual",
            "status": "failed",
            "delivery_status": "failed",
            "sender": norm_sender,
            "recipient": norm_recipient,
            "subject": final_subject,
            "error": str(exc),
            "message": f"Unexpected error during manual test run: {exc}",
        }


__all__ = [
    "create_ethereal_account",
    "send_automatic_test_run",
    "send_manual_test_run",
    "EtherealSMTP",
]


if __name__ == "__main__":
    print("Testing test_dispatcher.py...")
    test_ja = "山田様\nプロジェクトの仕様書ドラフトを送付いたします。ご確認よろしくお願いいたします。"
    test_en = "Dear Yamada-san,\nAttached is the project specification draft. Please review it at your convenience."
    test_subj = "Project Specification Draft / 仕様書ドラフト"
    test_ja_subj = "仕様書ドラフト送付"

    print("\n1. Testing Automatic Test Run...")
    auto_res = send_automatic_test_run(
        japanese_body=test_ja,
        english_body=test_en,
        subject=test_subj,
        japanese_subject=test_ja_subj,
    )
    print("Automatic result:", json.dumps(auto_res, indent=2, ensure_ascii=False))

    print("\n2. Testing Manual Test Run (custom sender, provider-free)...")
    manual_res = send_manual_test_run(
        sender_email="developer@company-domain.internal",
        recipient_email="client.partner@tokyo-enterprise.jp",
        japanese_body=test_ja,
        english_body=test_en,
        subject=test_subj,
        japanese_subject=test_ja_subj,
    )
    print("Manual result:", json.dumps(manual_res, indent=2, ensure_ascii=False))
