"""
End-to-End CLI Orchestrator Module.

Coordinates the bilingual email workflow:
1. write_email: Generates formal English email via NVIDIA AI Foundation Endpoints.
2. translate: Translates English text to Japanese via Google Translate.
3. email_sender: Dispatches styled dual-card HTML and plain-text email via SMTP.

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


def orchestrate(
    topic: str,
    to: Optional[str] = None,
    subject: Optional[str] = None,
    dry_run: bool = False,
    auto_confirm: bool = False,
) -> dict[str, Any]:
    """
    Runs the full end-to-end email translation pipeline:
    NVIDIA AI -> Google Translate -> SMTP delivery.
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

    # Determine subject: user override > parsed from LLM > fallback
    inferred_subject, cleaned_english_body = extract_subject_from_draft(english_draft)
    final_subject = subject.strip() if subject and subject.strip() else inferred_subject

    # Step 2: Translate to Japanese via Google Translate
    print("[2/3] Translating English email to Japanese via Google Translate...")
    try:
        # Translate the body (or full draft if subject wasn't isolated)
        japanese_translation = translate_english_to_japanese(cleaned_english_body)
    except Exception as exc:
        err_msg = f"Translation failed: {exc}"
        print(f"[ERROR] {err_msg}")
        return {"success": False, "message": err_msg}

    # Display console preview
    print(f"\n{'-'*70}")
    print("📋 EMAIL PREVIEW")
    print(f"{'-'*70}")
    print(f"Subject:    {final_subject}")
    print(f"Recipient:  {to if to else '[Not specified]'}")
    print(f"\n--- [English Draft] ---\n{cleaned_english_body}")
    print(f"\n--- [Japanese Translation] ---\n{japanese_translation}")
    print(f"{'-'*70}")

    # Step 3: Dispatch or Dry-run
    if dry_run:
        print("\n[3/3] [DRY-RUN] Execution completed. Delivery skipped (--dry-run flag enabled).")
        return {
            "success": True,
            "dry_run": True,
            "subject": final_subject,
            "english": cleaned_english_body,
            "japanese": japanese_translation,
            "message": "Dry-run succeeded.",
        }

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
  # Generate & translate in dry-run mode (no email sent):
  python -m email_trans.main --topic "Informing client for project completion" --dry-run

  # Full delivery with specified recipient and subject:
  python -m email_trans.main --topic "Meeting reschedule request" --to client@example.com --subject "Schedule Update"

  # Non-interactive automated dispatch (skip confirmation prompt):
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
        "--subject",
        "-s",
        type=str,
        help="Email subject line (extracted from draft if not provided).",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Preview generated English email and Japanese translation without sending via SMTP.",
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
    )

    return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
