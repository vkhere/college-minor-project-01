"""
Bilingual Email Translator - Streamlit Web Application
Powered by NVIDIA AI Foundation Endpoints, Google Translate, and Gmail SMTP.
Compatible with Python 3.10 - 3.14.2.
"""

import os
import sys
import time
import html
import streamlit as st
from dotenv import load_dotenv

# Ensure local packages can be imported
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

load_dotenv()

from email_trans.write_email import generate_email
from email_trans.translate import translate_english_to_japanese
from email_trans.email_sender import send_email, is_valid_email
from email_trans.test_dispatcher import send_automatic_test_run, send_manual_test_run
from email_trans.main import extract_subject_from_draft


def format_japanese_subject(text: str) -> str:
    """Formats translated Japanese subject text with a clean 【件名】 prefix if not already bracketed."""
    cleaned = text.strip()
    if not cleaned:
        return "【件名】ご連絡"
    if cleaned.startswith("【"):
        return cleaned
    if cleaned.lower().startswith("subject:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    if cleaned.startswith("件名:"):
        cleaned = cleaned[3:].strip()
    elif cleaned.startswith("件名："):
        cleaned = cleaned[3:].strip()
    return f"【件名】{cleaned}"


def resolve_dispatch_subject(format_choice: str, en_subject: str, ja_subject: str) -> str:
    """Builds the final subject line based on the selected dispatch format."""
    en_sub = en_subject.strip()
    ja_sub = ja_subject.strip()

    if "Bilingual" in format_choice:
        if ja_sub and en_sub:
            if ja_sub.startswith("【"):
                return f"{ja_sub} {en_sub}"
            else:
                return f"【{ja_sub}】 {en_sub}"
        elif ja_sub:
            return ja_sub
        elif en_sub:
            return en_sub
        return "Bilingual Communication / 業務連絡"
    elif "Japanese Only" in format_choice:
        return ja_sub or en_sub or "【件名】ご連絡"
    elif "English Only" in format_choice:
        return en_sub or ja_sub or "Bilingual Communication"

    return en_sub or ja_sub or "Bilingual Communication"


# ------------------------------------------------------------------------------
# Page Configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Bilingual Email Translator (EN ⇄ JA)",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------------------------------------------------------------------
# Custom CSS for Modern Styling & Bilingual Cards
# ------------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 0.4rem;
        margin-bottom: 0.5rem;
    }
    .badge-python { background-color: #E0F2FE; color: #0369A1; }
    .badge-nvidia { background-color: #DCFCE7; color: #15803D; }
    .badge-google { background-color: #FEF3C7; color: #B45309; }
    .badge-smtp { background-color: #F3E8FF; color: #7E22CE; }
    
    .card-jp {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-left: 5px solid #d63384;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .card-en {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-left: 5px solid #856404;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 14px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------------------------
if "topic_input" not in st.session_state:
    st.session_state.topic_input = ""
if "direct_text_input" not in st.session_state:
    st.session_state.direct_text_input = ""
if "direct_subject_input" not in st.session_state:
    st.session_state.direct_subject_input = ""
if "english_draft" not in st.session_state:
    st.session_state.english_draft = ""
if "japanese_body" not in st.session_state:
    st.session_state.japanese_body = ""
if "email_subject" not in st.session_state:
    st.session_state.email_subject = ""
if "japanese_subject" not in st.session_state:
    st.session_state.japanese_subject = ""
if "last_translated_sub_en" not in st.session_state:
    st.session_state.last_translated_sub_en = ""
if "last_translated_body_en" not in st.session_state:
    st.session_state.last_translated_body_en = ""
if "is_generated" not in st.session_state:
    st.session_state.is_generated = False
if "generation_error" not in st.session_state:
    st.session_state.generation_error = None
if "trigger_retry" not in st.session_state:
    st.session_state.trigger_retry = False

# ------------------------------------------------------------------------------
# Sidebar: Settings & Credentials
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ System Configuration")
    
    st.markdown("### 🔑 API Keys & Auth")
    env_nv_key = os.getenv("NVIDIA_API_KEY", "")
    api_key_input = st.text_input(
        "NVIDIA API Key",
        value=env_nv_key,
        type="password",
        help="Obtain a free developer API key with cloud credits from build.nvidia.com"
    )
    if api_key_input:
        os.environ["NVIDIA_API_KEY"] = api_key_input

    model_choice = st.selectbox(
        "NVIDIA Model",
        options=[
            "google/diffusiongemma-26b-a4b-it",
            "meta/llama-3.1-70b-instruct",
            "meta/llama-3.1-8b-instruct",
        ],
        index=0,
        help="Select the foundation model hosted on NVIDIA AI Foundation Endpoints"
    )
    os.environ["NVIDIA_MODEL"] = model_choice

    st.markdown("---")
    st.markdown("### 📬 Gmail SMTP Settings")
    env_sender = os.getenv("GMAIL_ADDRESS", os.getenv("SENDER_EMAIL", ""))
    env_password = os.getenv("GMAIL_APP_PASSWORD", os.getenv("SENDER_APP_PASSWORD", ""))

    sender_email = st.text_input(
        "Sender Gmail Address",
        value=env_sender,
        placeholder="your_email@gmail.com"
    )
    if sender_email:
        os.environ["GMAIL_ADDRESS"] = sender_email

    sender_password = st.text_input(
        "Gmail 16-Char App Password",
        value=env_password,
        type="password",
        help="Generate at myaccount.google.com/apppasswords (requires 2-Step Verification)"
    )
    if sender_password:
        os.environ["GMAIL_APP_PASSWORD"] = sender_password

    st.markdown("---")
    st.markdown("### 🛡️ Security Status")
    st.caption("✅ Secrets are read from `.env` or input safely. `.env` is strictly ignored by `.gitignore` and never committed.")
    
    st.markdown("---")
    st.caption("Built with Streamlit • Python 3.14.2 Ready")

# ------------------------------------------------------------------------------
# Main Content Area
# ------------------------------------------------------------------------------
st.markdown('<div class="main-header">📧 Bilingual Email Translator (EN ⇄ 日本語)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Draft professional correspondence with NVIDIA AI, translate with Google Translate, and dispatch via Gmail SMTP.</div>', unsafe_allow_html=True)

# Status Badges
st.markdown("""
<div>
    <span class="badge badge-python">🐍 Python 3.14.2 Ready</span>
    <span class="badge badge-nvidia">⚡ NVIDIA AI Cloud</span>
    <span class="badge badge-google">🌐 Google Translate</span>
    <span class="badge badge-smtp">🔒 SMTP TLS Encrypted</span>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Step 1: Input Mode Selection (AI Composition vs Direct Translation)
# ------------------------------------------------------------------------------
st.markdown("### 1️⃣ Choose Input Mode & Provide Content")

tab_ai, tab_direct = st.tabs([
    "🤖 Mode A: AI Compose & Translate (From Topic/Idea)",
    "⚡ Mode B: Direct Translate (Translate existing text/email)"
])

# --------------------- TAB A: AI COMPOSE & TRANSLATE ---------------------
with tab_ai:
    st.info("💡 **How it works:** Enter a short topic, idea, or bullet points. The NVIDIA AI will write a complete, formal corporate English email, which will then be translated to Japanese.")
    
    # Quick Example Topic Chips
    col_chips = st.columns([1, 1, 1, 1])
    with col_chips[0]:
        if st.button("🚀 Milestone Completed", use_container_width=True):
            st.session_state.topic_input = "Informing client that Project Milestone 1 has been completed on schedule with deliverables attached."
            st.session_state.topic_area = st.session_state.topic_input
            st.session_state.generation_error = None
            st.rerun()
    with col_chips[1]:
        if st.button("📅 Reschedule Meeting", use_container_width=True):
            st.session_state.topic_input = "Requesting to reschedule the technical sync from Thursday 3 PM to Friday 10 AM due to an unavoidable conflict."
            st.session_state.topic_area = st.session_state.topic_input
            st.session_state.generation_error = None
            st.rerun()
    with col_chips[2]:
        if st.button("💼 Delivery Update", use_container_width=True):
            st.session_state.topic_input = "Providing a weekly status report on system performance, bug fixes, and next sprint goals."
            st.session_state.topic_area = st.session_state.topic_input
            st.session_state.generation_error = None
            st.rerun()
    with col_chips[3]:
        if st.button("🤝 Partnership Proposal", use_container_width=True):
            st.session_state.topic_input = "Reaching out to explore a collaborative partnership between our software engineering teams."
            st.session_state.topic_area = st.session_state.topic_input
            st.session_state.generation_error = None
            st.rerun()

    topic_text = st.text_area(
        "Enter email topic, intent, or bullet points:",
        value=st.session_state.topic_input,
        placeholder="e.g. Informing client that the software integration phase is completed and ready for testing...",
        height=90,
        key="topic_area",
        help="Type your topic here and click the button below to generate and translate."
    )

    btn_generate_ai = st.button("✨ Generate Formal Email & Translate", type="primary", use_container_width=True, key="btn_ai")

    # Graceful error handling: Display warning, tip & retry button if a timeout or generation error occurred
    if st.session_state.get("generation_error"):
        err_info = st.session_state.generation_error
        if err_info.get("is_timeout"):
            st.warning(
                f"⚠️ **Request Timed Out**: {err_info.get('message')}\n\n"
                "The NVIDIA AI Cloud endpoint did not respond within the allocated timeframe despite retries."
            )
            st.info(
                "💡 **Tip:** Cloud GPU endpoints (such as NVIDIA AI Foundation Endpoints) occasionally experience "
                "momentary cold starts or high server queue latency during traffic spikes. "
                "Retrying typically connects to a warmed GPU instance immediately. "
                "You can also select a faster model (e.g., `meta/llama-3.1-8b-instruct`) in the sidebar."
            )
            col_retry, _ = st.columns([1, 2])
            with col_retry:
                if st.button("🔄 Retry Generation", type="primary", use_container_width=True, key="btn_retry_action"):
                    st.session_state.trigger_retry = True
                    st.session_state.generation_error = None
                    st.rerun()
        else:
            st.error(f"❌ Email generation failed: {err_info.get('message')}")
            col_retry, _ = st.columns([1, 2])
            with col_retry:
                if st.button("🔄 Retry Generation", use_container_width=True, key="btn_retry_generic"):
                    st.session_state.trigger_retry = True
                    st.session_state.generation_error = None
                    st.rerun()

    trigger_generate = btn_generate_ai or st.session_state.get("trigger_retry", False)

    if trigger_generate:
        st.session_state.trigger_retry = False
        target_topic = topic_text.strip() if topic_text and topic_text.strip() else st.session_state.get("topic_input", "").strip()

        if not target_topic:
            st.warning("⚠️ Please provide an email topic or select one of the quick presets above.")
            st.session_state.generation_error = None
        elif not os.getenv("NVIDIA_API_KEY"):
            st.error("❌ NVIDIA API Key is required for email generation. Please enter it in the sidebar or set NVIDIA_API_KEY in your .env file.")
            st.session_state.generation_error = None
        else:
            st.session_state.generation_error = None
            st.session_state.is_generated = False

            with st.spinner("🤖 Drafting formal English email via NVIDIA AI Cloud (may take 5-15s depending on server queue)..."):
                try:
                    raw_draft = generate_email(target_topic)
                    inferred_sub, cleaned_body = extract_subject_from_draft(raw_draft)
                    st.session_state.email_subject = inferred_sub
                    st.session_state.english_draft = cleaned_body
                except Exception as e:
                    err_msg = str(e)
                    is_timeout = "timeout" in err_msg.lower() or "timed out" in err_msg.lower()
                    st.session_state.generation_error = {
                        "is_timeout": is_timeout,
                        "message": err_msg
                    }
                    st.rerun()

            with st.spinner("🌐 Translating English email to Japanese using Google Translate..."):
                try:
                    ja_trans = translate_english_to_japanese(st.session_state.english_draft)
                    st.session_state.japanese_body = ja_trans

                    # Automatically translate English subject to Japanese
                    ja_sub_trans = translate_english_to_japanese(st.session_state.email_subject)
                    st.session_state.japanese_subject = format_japanese_subject(ja_sub_trans)

                    st.session_state.last_translated_sub_en = st.session_state.email_subject
                    st.session_state.last_translated_body_en = st.session_state.english_draft

                    st.session_state.is_generated = True
                    st.session_state.generation_error = None
                    st.success("🎉 Email generated and translated successfully! Review it in Step 2 below.")
                except Exception as e:
                    st.error(f"❌ Translation failed: {e}")
                    st.stop()

# --------------------- TAB B: DIRECT TEXT TRANSLATION ---------------------
with tab_direct:
    st.info("💡 **How it works:** Already have text or an email written? Type or paste it here (like *'hello'* or a full message) and click below to translate it directly to Japanese using Google Translate without invoking the LLM.")
    
    direct_sub_input = st.text_input(
        "Optional Subject Line (English):",
        value=st.session_state.direct_subject_input,
        placeholder="e.g. Project Status Update or Milestone Review",
        key="direct_sub_area",
        help="Optional: Enter a subject line to translate directly alongside the body."
    )
    st.session_state.direct_subject_input = direct_sub_input

    direct_input = st.text_area(
        "Enter English text or email body to translate:",
        value=st.session_state.direct_text_input,
        placeholder="e.g. Hello, we are pleased to inform you that our project is ready for review.",
        height=110,
        key="direct_area",
    )
    st.session_state.direct_text_input = direct_input

    btn_direct_trans = st.button("🌐 Translate Directly to Japanese", type="primary", use_container_width=True, key="btn_direct")

    if btn_direct_trans:
        if not direct_input.strip() and not direct_sub_input.strip():
            st.warning("⚠️ Please enter some English text or a subject line to translate.")
        else:
            with st.spinner("🌐 Translating directly using Google Translate..."):
                try:
                    if direct_input.strip():
                        ja_trans = translate_english_to_japanese(direct_input.strip())
                        st.session_state.english_draft = direct_input.strip()
                        st.session_state.japanese_body = ja_trans
                    else:
                        st.session_state.english_draft = ""
                        st.session_state.japanese_body = ""

                    if direct_sub_input.strip():
                        ja_sub_trans = translate_english_to_japanese(direct_sub_input.strip())
                        st.session_state.email_subject = direct_sub_input.strip()
                        st.session_state.japanese_subject = format_japanese_subject(ja_sub_trans)
                    else:
                        st.session_state.email_subject = "Communication / 業務連絡"
                        st.session_state.japanese_subject = "【件名】ご連絡"

                    st.session_state.last_translated_sub_en = st.session_state.email_subject
                    st.session_state.last_translated_body_en = st.session_state.english_draft

                    st.session_state.is_generated = True
                    st.session_state.generation_error = None
                    st.success("🎉 Translation completed! Review it in Step 2 below.")
                except Exception as e:
                    st.error(f"❌ Direct translation failed: {e}")
                    st.stop()

# ------------------------------------------------------------------------------
# Step 2: Review, Edit & Live Preview
# ------------------------------------------------------------------------------
if st.session_state.is_generated:
    st.markdown("---")
    st.markdown("### 2️⃣ Review & Edit Content")
    
    col_sub_en, col_sub_ja = st.columns(2)
    with col_sub_en:
        edited_sub_en = st.text_input(
            "📝 English Subject Line:",
            value=st.session_state.email_subject,
            help="Press Enter to apply",
        )
        if edited_sub_en != st.session_state.get("last_translated_sub_en"):
            with st.spinner("🌐 Auto-translating Subject Line to Japanese..."):
                ja_sub_trans = translate_english_to_japanese(edited_sub_en)
                st.session_state.japanese_subject = format_japanese_subject(ja_sub_trans)
                st.session_state.last_translated_sub_en = edited_sub_en
                st.session_state.email_subject = edited_sub_en
            st.rerun()
        else:
            st.session_state.email_subject = edited_sub_en

    with col_sub_ja:
        edited_sub_ja = st.text_input(
            "🌸 Japanese Subject Line (件名):",
            value=st.session_state.japanese_subject,
        )
        st.session_state.japanese_subject = edited_sub_ja

    col_edit_en, col_edit_ja = st.columns(2)
    with col_edit_en:
        st.markdown("**📝 English Email Draft** *(Editable)*")
        edited_en = st.text_area(
            "English body",
            value=st.session_state.english_draft,
            height=280,
            label_visibility="collapsed",
            help="Press Ctrl+Enter to apply",
        )
        if edited_en != st.session_state.get("last_translated_body_en"):
            with st.spinner("🌐 Auto-translating Email Draft to Japanese..."):
                ja_body_trans = translate_english_to_japanese(edited_en)
                st.session_state.japanese_body = ja_body_trans
                st.session_state.last_translated_body_en = edited_en
                st.session_state.english_draft = edited_en
            st.rerun()
        else:
            st.session_state.english_draft = edited_en
        
        if st.button("🔄 Re-translate to Japanese", help="Re-translates current English subject and body to Japanese"):
            with st.spinner("Translating..."):
                st.session_state.japanese_body = translate_english_to_japanese(st.session_state.english_draft)
                st.session_state.last_translated_body_en = st.session_state.english_draft
                if st.session_state.email_subject.strip():
                    ja_sub_trans = translate_english_to_japanese(st.session_state.email_subject.strip())
                    st.session_state.japanese_subject = format_japanese_subject(ja_sub_trans)
                    st.session_state.last_translated_sub_en = st.session_state.email_subject
                st.rerun()

    with col_edit_ja:
        st.markdown("**🌸 Japanese Translation (日本語)** *(Editable)*")
        edited_ja = st.text_area(
            "Japanese body",
            value=st.session_state.japanese_body,
            height=280,
            label_visibility="collapsed",
        )
        st.session_state.japanese_body = edited_ja

    # Visual HTML Email Preview
    with st.expander("👁️ View Live HTML Email Preview (Recipient View)", expanded=True):
        st.caption("This matches the exact styling rendered in the recipient's email client (Gmail, Outlook, iOS):")
        
        preview_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: 10px auto; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="background: #f8f9fa; padding: 18px; border-left: 4px solid #d63384; border-radius: 8px; margin-bottom: 16px;">
                <h4 style="color: #d63384; margin-top: 0; margin-bottom: 8px; font-size: 15px;">🇯🇵 Japanese Translation (日本語)</h4>
                <div style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #e2e8f0;">
                    <span style="font-size: 12px; font-weight: 700; color: #d63384; text-transform: uppercase;">件名:</span>
                    <span style="font-size: 14px; font-weight: 600; color: #1e293b; margin-left: 6px;">{html.escape(st.session_state.japanese_subject)}</span>
                </div>
                <div style="font-size: 15px; line-height: 1.6; color: #1e293b; white-space: pre-wrap;">{html.escape(st.session_state.japanese_body)}</div>
            </div>
            <div style="background: #fff3cd; padding: 18px; border-left: 4px solid #856404; border-radius: 8px;">
                <h4 style="color: #856404; margin-top: 0; margin-bottom: 8px; font-size: 15px;">🇬🇧 Original (English)</h4>
                <div style="margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px dashed #ffeeba;">
                    <span style="font-size: 12px; font-weight: 700; color: #856404; text-transform: uppercase;">Subject:</span>
                    <span style="font-size: 14px; font-weight: 600; color: #475569; margin-left: 6px;">{html.escape(st.session_state.email_subject)}</span>
                </div>
                <div style="font-size: 14px; line-height: 1.6; color: #475569; white-space: pre-wrap;">{html.escape(st.session_state.english_draft)}</div>
            </div>
            <hr style="margin-top: 24px; border: none; border-top: 1px solid #e2e8f0;">
            <p style="font-size: 11px; color: #94a3b8; text-align: center; margin-bottom: 0;">
                Generated by Bilingual Email Translator • Powered by NVIDIA AI & Google Translate
            </p>
        </div>
        """
        st.html(preview_html)

    # --------------------------------------------------------------------------
    # Step 3: Dispatch via Gmail SMTP
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 3️⃣ Dispatch via SMTP")
    
    subject_dispatch_format = st.radio(
        "Subject Dispatch Format:",
        options=[
            "🌐 Bilingual: 【Japanese Subject】 English Subject",
            "🇯🇵 Japanese Only",
            "🇬🇧 English Only",
        ],
        index=0,
        help="Select the format for the email subject header when dispatched to recipients."
    )

    final_dispatch_subject = resolve_dispatch_subject(
        subject_dispatch_format,
        st.session_state.email_subject,
        st.session_state.japanese_subject
    )
    st.caption(f"📨 **Subject to be dispatched:** `{final_dispatch_subject}`")

    dispatch_mode = st.radio(
        "Select Dispatch Mode:",
        options=[
            "🚀 Live Production Dispatch (Send to Real Recipient via Gmail SMTP)",
            "🧪 Manual Dry-run with sending (Any Mail Provider: Custom Sender & Recipient)",
            "⚡ Automatic Dry-run with sending (100% Automated: 2 Temp Inboxes)",
        ],
        index=0,
        help="Select the dispatch mode: Live production dispatch via Gmail SMTP, Manual test with arbitrary sender/recipient addresses, or 100% Automated test using 2 disposable inboxes.",
    )

    if "🚀 Live Production Dispatch" in dispatch_mode:
        recipient_to = st.text_input(
            "Recipient Email Address:",
            placeholder="client@company.jp or colleague@example.com",
            help="Destination email address for live delivery via Gmail SMTP.",
        )

        col_btn_send, _ = st.columns([1, 2])
        with col_btn_send:
            btn_send = st.button("🚀 Send Email Now", type="primary", use_container_width=True)

        if btn_send:
            recipient_clean = recipient_to.strip()
            if not recipient_clean:
                st.error("❌ Recipient email address cannot be empty.")
            elif not is_valid_email(recipient_clean):
                st.error(f"❌ '{recipient_clean}' is not a valid email address.")
            else:
                current_sender = os.getenv("GMAIL_ADDRESS", os.getenv("SENDER_EMAIL", ""))
                current_pw = os.getenv("GMAIL_APP_PASSWORD", os.getenv("SENDER_APP_PASSWORD", ""))
                
                if not current_sender or not current_pw:
                    st.error("❌ Gmail sender credentials missing. Please configure your Gmail Address and App Password in the sidebar or .env.")
                else:
                    with st.spinner(f"📨 Connecting to smtp.gmail.com:587 via STARTTLS and dispatching to {recipient_clean}..."):
                        result = send_email(
                            sender_email=current_sender,
                            sender_password=current_pw,
                            recipient_email=recipient_clean,
                            subject=final_dispatch_subject,
                            japanese_body=st.session_state.japanese_body,
                            english_body=st.session_state.english_draft,
                            japanese_subject=st.session_state.japanese_subject,
                        )
                        
                        if result.get("success"):
                            st.balloons()
                            st.success(f"✅ {result.get('message')}")
                        else:
                            st.error(f"❌ {result.get('message')}")

    elif "🧪 Manual Dry-run with sending" in dispatch_mode:
        st.info("💡 **Provider-Free Test Dispatch:** The sender email is not restricted to Gmail! Enter any sender domain (e.g., `alice@company.com`, `user@outlook.com`, `team@corp.io`). Zero Gmail App Passwords required.")
        col_sender, col_recip = st.columns(2)
        with col_sender:
            env_sender_val = os.getenv("GMAIL_ADDRESS", os.getenv("SENDER_EMAIL", ""))
            sender_manual = st.text_input(
                "Sender Email Address (From):",
                value=env_sender_val or "alice@company.com",
                placeholder="alice@company.com or user@outlook.com",
                help="Provider-independent sender address. Does NOT need to be Gmail!",
            )
        with col_recip:
            recipient_manual = st.text_input(
                "Recipient Email Address (To):",
                placeholder="client@company.jp or colleague@example.com",
                help="Recipient email address to receive the test email.",
            )

        col_btn_manual, _ = st.columns([1, 2])
        with col_btn_manual:
            btn_manual = st.button("🧪 Send Manual Test Email", type="primary", use_container_width=True)

        if btn_manual:
            sender_clean = sender_manual.strip()
            recipient_clean = recipient_manual.strip()

            if not sender_clean:
                st.error("❌ Sender email address cannot be empty.")
            elif not is_valid_email(sender_clean):
                st.error(f"❌ '{sender_clean}' is not a valid email address.")
            elif not recipient_clean:
                st.error("❌ Recipient email address cannot be empty.")
            elif not is_valid_email(recipient_clean):
                st.error(f"❌ '{recipient_clean}' is not a valid email address.")
            else:
                with st.spinner(f"🧪 Dispatching manual test email from {sender_clean} to {recipient_clean} via sandbox relay..."):
                    result = send_manual_test_run(
                        sender_email=sender_clean,
                        recipient_email=recipient_clean,
                        japanese_body=st.session_state.japanese_body,
                        english_body=st.session_state.english_draft,
                        subject=final_dispatch_subject,
                        japanese_subject=st.session_state.japanese_subject,
                    )

                if result.get("success"):
                    st.balloons()
                    with st.container(border=True):
                        st.success("🎉 **Manual Test Email Delivered Successfully!**")
                        st.markdown(f"- 📤 **Sender Email Address (From):** `{result.get('sender', sender_clean)}` *(Provider-Free / Non-Gmail)*")
                        st.markdown(f"- 📥 **Recipient Email Address (To):** `{result.get('recipient', recipient_clean)}`")
                        st.markdown(f"- 📨 **Dispatched Subject Line:** `{result.get('subject', final_dispatch_subject)}`")
                        st.markdown(f"- 🔒 **Delivery Relay:** `{result.get('smtp_host', 'smtp.ethereal.email')}:{result.get('smtp_port', 587)}` *(STARTTLS)*")
                        st.markdown("- ✅ **Dual-Card Bilingual MIME formatting confirmed delivered.**")
                        
                        preview_url = result.get("preview_url")
                        if preview_url:
                            st.markdown("---")
                            st.link_button("🌐 View Delivered Email in Web Viewer", url=preview_url, type="primary")
                            st.caption(f"Direct link: [{preview_url}]({preview_url})")
                else:
                    st.error(f"❌ {result.get('message') or result.get('error')}")

    elif "⚡ Automatic Dry-run with sending" in dispatch_mode:
        st.info("⚡ **100% Automated Communication Self-Test:** Zero configuration or credentials needed! Automatically provisions 2 temporary disposable inboxes on the fly, connects to SMTP via STARTTLS, transmits the bilingual email, and lets you view the delivered email in the web viewer.")

        col_btn_auto, _ = st.columns([1, 2])
        with col_btn_auto:
            btn_auto = st.button("⚡ Run Automated Communication Test", type="primary", use_container_width=True)

        if btn_auto:
            progress_slot = st.empty()
            
            with progress_slot.container():
                with st.spinner("⏳ [1/3] Provisioning 2 temporary inboxes..."):
                    time.sleep(0.6)
            
            with progress_slot.container():
                with st.spinner("⏳ [2/3] Connecting to SMTP on port 587 via STARTTLS..."):
                    result = send_automatic_test_run(
                        japanese_body=st.session_state.japanese_body,
                        english_body=st.session_state.english_draft,
                        subject=final_dispatch_subject,
                        japanese_subject=st.session_state.japanese_subject,
                    )

            progress_slot.empty()

            if result.get("success"):
                st.success("🎉 **[3/3] Dispatched!** Communication test completed successfully.")
                st.balloons()
                with st.container(border=True):
                    st.markdown("### ⚡ Automated Communication Test Results")
                    st.markdown(f"- 📤 **Generated Temporary Sender:** `{result.get('sender')}`")
                    st.markdown(f"- 📥 **Generated Temporary Recipient:** `{result.get('recipient')}`")
                    st.markdown(f"- 📨 **Dispatched Subject:** `{result.get('subject', final_dispatch_subject)}`")
                    st.markdown(f"- 🔒 **Transport:** Ethereal SMTP Relay (Port 587, STARTTLS)")
                    
                    preview_url = result.get("preview_url")
                    if preview_url:
                        st.markdown("---")
                        st.link_button("🔗 View Received Email in Web Inbox", url=preview_url, type="primary")
                        st.caption(f"Direct link: [{preview_url}]({preview_url})")
            else:
                st.error(f"❌ {result.get('message') or result.get('error')}")
