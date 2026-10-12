"""
Email Translator Package.

Bilingual English-to-Japanese email automation pipeline:
1. write_email: Formulates formal English emails via NVIDIA AI Foundation Endpoints.
2. translate: Translates English text to natural Japanese via Google Translate.
3. email_sender: Dispatches bilingual dual-card HTML & plain-text emails via SMTP.
"""

from email_trans.write_email import generate_email
from email_trans.translate import translate_english_to_japanese
from email_trans.email_sender import send_email
from email_trans.test_dispatcher import send_automatic_test_run, send_manual_test_run

__all__ = [
    "generate_email",
    "translate_english_to_japanese",
    "send_email",
    "send_automatic_test_run",
    "send_manual_test_run",
]

