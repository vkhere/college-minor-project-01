"""
End-to-End CLI Orchestrator Module.

Coordinates the bilingual email workflow:
1. write_email: Generates formal English email via NVIDIA AI Foundation Endpoints.
2. translate: Translates English text to Japanese via Google Translate.
3. email_sender: Dispatches styled dual-card HTML and plain-text email via SMTP.
4. test_dispatcher: Executes provider-independent dry-runs (Automatic & Manual)
   via disposable Ethereal relays with online web preview links.

Compatible with Python 3.14.2.
"""

import os
import sys
import argparse
from typing import Any, Optional

# Ensure project root is available in sys.path for direct execution
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

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

from email_trans.write_email import generate_email
from email_trans.translate import translate_english_to_japanese
from email_trans.email_sender import send_email, is_valid_email
from email_trans.test_dispatcher import send_automatic_test_run, send_manual_test_run


def extract_subject_from_draft(text: str, default_subject: str = "Bilingual Communication / 業務連絡") -> tuple[str, str]:
    """
    Extracts Subject header if the LLM output starts with 'Subject: ...'.
    Returns (subject, remaining_body).
    """
    lines = text.strip().splitlines()
    if not lines:
        return default_subject, text

    first_line = lines[0].strip()
    if first_line.lower().startswith("subject:"):
        extracted_subject = first_line.split(":", 1)[1].strip()
        remaining_body = "\n".join(lines[1:]).strip()
        return extracted_subject or default_subject, remaining_body

    return default_subject, text.strip()


def console_preview(
    english_subject: str,
    japanese_subject: str,
    recipient: Optional[str] = None,
    english_body: str = "",
    japanese_body: str = "",
    **kwargs: Any,
) -> None:
    """
    Displays bilingual email CLI preview with English and Japanese subjects.
    """
    clean_ja = japanese_subject.strip()
    bracketed_ja = clean_ja if (clean_ja.startswith("【") and clean_ja.endswith("】")) else f"【{clean_ja}】"
    print(f"\n{'-'*70}")
    print("📋 EMAIL PREVIEW")
    print(f"{'-'*70}")
    print(f"Subject (EN): {english_subject}")
    print(f"Subject (JA): {bracketed_ja}")
    print(f"Recipient:    {recipient if recipient else '[Not specified]'}")
    print(f"\n--- [English Draft] ---\n{english_body}")
    print(f"\n--- [Japanese Translation] ---\n{japanese_body}")
    print(f"{'-'*70}")


# Backward-compatible alias
print_console_preview = console_preview


def orchestrate(
    topic: str,
    to: Optional[str] = None,
    subject: Optional[str] = None,
    dry_run: bool = False,
    auto_confirm: bool = False,
    auto_test: bool = False,
    manual_test: bool = False,
    from_email: Optional[str] = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Runs the full end-to-end email translation pipeline:
    NVIDIA AI -> Google Translate -> SMTP delivery / Dry-run testing.

    Modes:
    - Standard SMTP delivery: Sends email to recipient via configured SMTP credentials.
    - Dry-Run (--dry-run): Local preview only without network dispatch.
    - Automatic Dry-Run (--auto-test): Fully automated test run provisioning 2 disposable
      inboxes and sending via Ethereal SMTP with online web preview link.
    - Manual Dry-Run (--manual-test): Provider-independent test run supporting any custom
      sender and recipient, routed via test SMTP relay with online web preview link.
    """
    if not topic or not topic.strip():
        return {"success": False, "message": "Email topic cannot be empty."}

    print(f"\n{'='*70}")
    print("🚀 BILINGUAL EMAIL TRANSLATION PIPELINE")
    print(f"{'='*70}")
    print(f"[*] Topic: '{topic.strip()}'")

    # Step 1: Draft Email via NVIDIA AI Endpoint
    print("\n[1/3] Generating formal English email draft via NVIDIA AI Endpoint...")
    try:
        english_draft = generate_email(topic.strip())
    except Exception as exc:
        err_msg = f"Email generation failed: {exc}"
        print(f"[ERROR] {err_msg}")
        return {"success": False, "message": err_msg}

    # Extract inferred subject from draft and translate to Japanese
    inferred_subject, cleaned_english_body = extract_subject_from_draft(english_draft)
    try:
        raw_ja_subject = translate_english_to_japanese(inferred_subject).strip()
    except Exception as exc:
        print(f"[WARN] Failed to translate inferred subject to Japanese: {exc}")
        raw_ja_subject = inferred_subject

    clean_ja_sub = raw_ja_subject.strip()
    if clean_ja_sub.startswith("【") and clean_ja_sub.endswith("】"):
        clean_ja_sub = clean_ja_sub[1:-1].strip()
    bracketed_ja_subject = f"【{clean_ja_sub}】"

    english_subject = inferred_subject
    if subject and subject.strip():
        final_subject = subject.strip()
        english_subject = subject.strip()
    else:
        final_subject = f"{bracketed_ja_subject} {english_subject}"

    # Step 2: Translate to Japanese via Google Translate
    print("[2/3] Translating English email to Japanese via Google Translate...")
    try:
        # Translate the body (or full draft if subject wasn't isolated)
        japanese_translation = translate_english_to_japanese(cleaned_english_body)
    except Exception as exc:
        err_msg = f"Translation failed: {exc}"
        print(f"[ERROR] {err_msg}")
        return {"success": False, "message": err_msg}

    # Display console preview with both English and Japanese subjects
    preview_recipient = to
    if not preview_recipient and auto_test:
        preview_recipient = "[Auto-provisioned test inbox]"
    console_preview(
        english_subject=english_subject,
        japanese_subject=bracketed_ja_subject,
        recipient=preview_recipient,
        english_body=cleaned_english_body,
        japanese_body=japanese_translation,
    )

    # Step 3: Dispatch or Dry-run / Test Run

    # Mode 1: Automatic Dry-Run (Provider-independent, zero credentials)
    if auto_test:
        print("\n[3/3] [AUTO-TEST] Running Automatic Dry-Run (Provider-Independent)...")
        print("      Auto-provisioning 2 temporary inboxes via Ethereal...")
        test_result = send_automatic_test_run(
            japanese_body=japanese_translation,
            english_body=cleaned_english_body,
            subject=final_subject,
            japanese_subject=bracketed_ja_subject,
        )

        if test_result.get("success"):
            print(f"\n{'='*70}")
            print("✅ AUTOMATIC DRY-RUN COMPLETED")
            print(f"{'='*70}")
            print(f"[*] Delivery:     Delivered via Ethereal SMTP STARTTLS ({test_result.get('smtp_host')}:{test_result.get('smtp_port')})")
            print(f"[*] Temp Sender:  {test_result.get('sender')}")
            print(f"[*] Temp Recip:   {test_result.get('recipient')}")
            print(f"[*] Subject:      {test_result.get('subject')}")
            print(f"[*] Web Preview:  {test_result.get('preview_url')}")
            print(f"{'='*70}\n")
        else:
            print(f"\n[ERROR] Automatic dry-run failed: {test_result.get('message')}")

        return test_result

    # Mode 2: Manual Dry-Run (Provider-independent, custom sender & recipient)
    if manual_test:
        print("\n[3/3] [MANUAL-TEST] Preparing Manual Dry-Run (Provider-Independent)...")
        sender = (
            from_email
            or kwargs.get("sender")
            or kwargs.get("sender_email")
            or os.getenv("SENDER_EMAIL")
            or os.getenv("GMAIL_ADDRESS")
        )

        if not sender or not str(sender).strip():
            if sys.stdin.isatty():
                try:
                    sender = input("Enter sender email (any provider, e.g. me@outlook.com): ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nOperation aborted by user.")
                    return {"success": False, "message": "Operation aborted."}

        if not sender or not is_valid_email(str(sender).strip()):
            err_msg = f"Invalid or missing sender email address: '{sender}'. Specify with --from / -f."
            print(f"[ERROR] {err_msg}")
            return {"success": False, "message": err_msg}

        if not to or not str(to).strip():
            if sys.stdin.isatty():
                try:
                    to = input("Enter recipient email address: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\nOperation aborted by user.")
                    return {"success": False, "message": "Operation aborted."}

        if not to or not is_valid_email(str(to).strip()):
            err_msg = f"Invalid or missing recipient email address: '{to}'. Specify with --to / -r."
            print(f"[ERROR] {err_msg}")
            return {"success": False, "message": err_msg}

        norm_sender = str(sender).strip()
        norm_to = str(to).strip()

        if not auto_confirm and sys.stdin.isatty():
            try:
                choice = input(f"Dispatch manual test run from '{norm_sender}' to '{norm_to}'? [y/N]: ").strip().lower()
                if choice not in ("y", "yes"):
                    print("[INFO] Manual test dispatch canceled by user.")
                    return {"success": False, "message": "Delivery canceled by user."}
            except (KeyboardInterrupt, EOFError):
                print("\nOperation aborted by user.")
                return {"success": False, "message": "Operation aborted."}

        print("      Routing transmission via provisioned test SMTP relay with custom headers...")
        test_result = send_manual_test_run(
            sender_email=norm_sender,
            recipient_email=norm_to,
            japanese_body=japanese_translation,
            english_body=cleaned_english_body,
            subject=final_subject,
            japanese_subject=bracketed_ja_subject,
        )

        if test_result.get("success"):
            print(f"\n{'='*70}")
            print("✅ MANUAL DRY-RUN COMPLETED")
            print(f"{'='*70}")
            print(f"[*] Transmission: Delivered via test SMTP relay ({test_result.get('smtp_host')}:{test_result.get('smtp_port')})")
            print(f"[*] Sender:       {test_result.get('sender')}")
            print(f"[*] Recipient:    {test_result.get('recipient')}")
            print(f"[*] Subject:      {test_result.get('subject')}")
            print(f"[*] Web Preview:  {test_result.get('preview_url')}")
            print(f"{'='*70}\n")
        else:
            print(f"\n[ERROR] Manual test run failed: {test_result.get('message')}")

        return test_result

    # Mode 3: Local Dry-run (No email sent)
    if dry_run:
        print("\n[3/3] [DRY-RUN] Execution completed. Delivery skipped (--dry-run flag enabled).")
        return {
            "success": True,
            "dry_run": True,
            "subject": final_subject,
            "english_subject": english_subject,
            "japanese_subject": bracketed_ja_subject,
            "english": cleaned_english_body,
            "japanese": japanese_translation,
            "message": "Dry-run succeeded.",
        }

    # Mode 4: Standard SMTP dispatch
    print("\n[3/3] Preparing SMTP dispatch...")
    if not to or not to.strip():
        # In interactive terminal, allow user to input recipient
        if sys.stdin.isatty():
            try:
                to = input("Enter recipient email address: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nOperation aborted by user.")
                return {"success": False, "message": "Operation aborted."}

    if not to or not is_valid_email(to):
        err_msg = f"Invalid or missing recipient email address: '{to}'."
        print(f"[ERROR] {err_msg}")
        return {"success": False, "message": err_msg}

    # User confirmation prompt (unless --yes flag is given)
    if not auto_confirm and sys.stdin.isatty():
        try:
            choice = input(f"Send this email to '{to}'? [y/N]: ").strip().lower()
            if choice not in ("y", "yes"):
                print("[INFO] Email dispatch canceled by user.")
                return {"success": False, "message": "Delivery canceled by user."}
        except (KeyboardInterrupt, EOFError):
            print("\nOperation aborted by user.")
            return {"success": False, "message": "Operation aborted."}

    send_result = send_email(
        recipient_email=to,
        subject=final_subject,
        japanese_body=japanese_translation,
        english_body=cleaned_english_body,
        japanese_subject=bracketed_ja_subject,
    )

    if send_result.get("success"):
        print(f"[SUCCESS] {send_result.get('message')}")
    else:
        print(f"[ERROR] {send_result.get('message')}")

    return send_result


def build_parser() -> argparse.ArgumentParser:
    """Creates the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Bilingual English-to-Japanese Email Translator (NVIDIA AI + Google Translate + SMTP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 1. Automatic Zero-Configuration Dry-Run (No email addresses or credentials needed!):
  python -m email_trans.main --topic "Project delivery update" --auto-test

  # 2. Manual Dry-Run with custom sender and recipient (Provider-Independent!):
  python -m email_trans.main --topic "Meeting reschedule" --manual-test --from user@outlook.com --to client@partner.jp

  # 3. Local preview only (dry-run without network dispatch):
  python -m email_trans.main --topic "Informing client for project completion" --dry-run

  # 4. Production delivery via configured SMTP (Gmail / Custom):
  python -m email_trans.main --topic "Meeting reschedule request" --to client@example.com --subject "Schedule Update"

  # 5. Non-interactive automated production dispatch (skip confirmation prompt):
  python -m email_trans.main --topic "Project delivery" --to client@example.com --yes
        """,
    )
    parser.add_argument(
        "--topic",
        "-t",
        type=str,
        help="Topic or short summary of the email to generate.",
    )
    parser.add_argument(
        "--to",
        "-r",
        "--recipient",
        type=str,
        help="Recipient email address.",
    )
    parser.add_argument(
        "--from",
        "-f",
        "--from-email",
        "--sender",
        dest="from_email",
        type=str,
        help="Sender email address (any provider, not restricted to Gmail; e.g. me@outlook.com, dev@company.com). Used with --manual-test.",
    )
    parser.add_argument(
        "--subject",
        "-s",
        type=str,
        help="Email subject line (extracted from draft if not provided).",
    )
    parser.add_argument(
        "--auto-test",
        "-a",
        action="store_true",
        help="Run an Automatic Dry-Run with live SMTP transmission. Requires NO email addresses and NO credentials. "
             "Auto-provisions 2 temporary inboxes, delivers via SMTP STARTTLS, and prints the web preview link.",
    )
    parser.add_argument(
        "--manual-test",
        "-m",
        action="store_true",
        help="Run a Manual Dry-Run with live SMTP transmission. Provider-independent: accepts any sender (--from / -f) "
             "and recipient (--to / -r) without requiring Gmail credentials. Prints transmission logs and web preview link.",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Preview generated English email and Japanese translation locally without sending via SMTP.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Automatically confirm and send email without interactive prompt.",
    )
    return parser


def main() -> int:
    """CLI Entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    # Validate mutually exclusive dry-run flags if multiple specified
    active_test_modes = sum(bool(m) for m in [args.auto_test, args.manual_test, args.dry_run])
    if active_test_modes > 1:
        print(
            "[ERROR] Conflicting options: Please specify only one of --auto-test, --manual-test, or --dry-run.",
            file=sys.stderr,
        )
        return 1

    topic = args.topic
    if not topic:
        if sys.stdin.isatty():
            try:
                topic = input("Enter email topic/summary: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                return 1
        else:
            parser.print_help()
            print("\n[ERROR] --topic argument is required when running non-interactively.", file=sys.stderr)
            return 1

    if not topic:
        print("[ERROR] Email topic cannot be empty.", file=sys.stderr)
        return 1

    result = orchestrate(
        topic=topic,
        to=args.to,
        subject=args.subject,
        dry_run=args.dry_run,
        auto_confirm=args.yes,
        auto_test=args.auto_test,
        manual_test=args.manual_test,
        from_email=args.from_email,
    )

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
