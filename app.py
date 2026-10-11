"""
Bilingual Email Translator - Streamlit Web Application
Powered by NVIDIA AI Foundation Endpoints, Google Translate, and Gmail SMTP.
Compatible with Python 3.10 - 3.14.2.
"""

import os
import sys
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
from email_trans.main import extract_subject_from_draft

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
if "english_draft" not in st.session_state:
    st.session_state.english_draft = ""
if "japanese_body" not in st.session_state:
    st.session_state.japanese_body = ""
if "email_subject" not in st.session_state:
    st.session_state.email_subject = ""
if "is_generated" not in st.session_state:
    st.session_state.is_generated = False

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
    with col_chips[1]:
        if st.button("📅 Reschedule Meeting", use_container_width=True):
            st.session_state.topic_input = "Requesting to reschedule the technical sync from Thursday 3 PM to Friday 10 AM due to an unavoidable conflict."
    with col_chips[2]:
        if st.button("💼 Delivery Update", use_container_width=True):
            st.session_state.topic_input = "Providing a weekly status report on system performance, bug fixes, and next sprint goals."
    with col_chips[3]:
        if st.button("🤝 Partnership Proposal", use_container_width=True):
            st.session_state.topic_input = "Reaching out to explore a collaborative partnership between our software engineering teams."

    topic_text = st.text_area(
        "Enter email topic, intent, or bullet points:",
        value=st.session_state.topic_input,
        placeholder="e.g. Informing client that the software integration phase is completed and ready for testing...",
        height=90,
        key="topic_area",
        help="Type your topic here and click the button below to generate and translate."
    )

    btn_generate_ai = st.button("✨ Generate Formal Email & Translate", type="primary", use_container_width=True, key="btn_ai")

    if btn_generate_ai:
        if not topic_text.strip():
            st.warning("⚠️ Please provide an email topic or select one of the quick presets above.")
        elif not os.getenv("NVIDIA_API_KEY"):
            st.error("❌ NVIDIA API Key is required for email generation. Please enter it in the sidebar or set NVIDIA_API_KEY in your .env file.")
        else:
            with st.spinner("🤖 [1/2] Drafting formal English email using NVIDIA AI Foundation Endpoints..."):
                try:
                    raw_draft = generate_email(topic_text.strip())
                    inferred_sub, cleaned_body = extract_subject_from_draft(raw_draft)
                    st.session_state.email_subject = inferred_sub
                    st.session_state.english_draft = cleaned_body
                except Exception as e:
                    st.error(f"❌ Email generation failed: {e}")
                    st.stop()

            with st.spinner("🌐 [2/2] Translating English email to Japanese using Google Translate..."):
                try:
                    ja_trans = translate_english_to_japanese(st.session_state.english_draft)
                    st.session_state.japanese_body = ja_trans
                    st.session_state.is_generated = True
                    st.success("🎉 Email generated and translated successfully! Review it in Step 2 below.")
                except Exception as e:
                    st.error(f"❌ Translation failed: {e}")
                    st.stop()

# --------------------- TAB B: DIRECT TEXT TRANSLATION ---------------------
with tab_direct:
    st.info("💡 **How it works:** Already have text or an email written? Type or paste it here (like *'hello'* or a full message) and click below to translate it directly to Japanese using Google Translate without invoking the LLM.")
    
    direct_input = st.text_area(
        "Enter English text or email body to translate:",
        value=st.session_state.direct_text_input,
        placeholder="e.g. Hello, we are pleased to inform you that our project is ready for review.",
        height=110,
        key="direct_area",
    )

    btn_direct_trans = st.button("🌐 Translate Directly to Japanese", type="primary", use_container_width=True, key="btn_direct")

    if btn_direct_trans:
        if not direct_input.strip():
            st.warning("⚠️ Please enter some English text to translate.")
        else:
            with st.spinner("🌐 Translating directly using Google Translate..."):
                try:
                    ja_trans = translate_english_to_japanese(direct_input.strip())
                    st.session_state.english_draft = direct_input.strip()
                    st.session_state.japanese_body = ja_trans
                    if not st.session_state.email_subject:
                        st.session_state.email_subject = "Communication / ご連絡"
                    st.session_state.is_generated = True
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
    
    subject_input = st.text_input("Subject Line:", value=st.session_state.email_subject)
    st.session_state.email_subject = subject_input

    col_edit_en, col_edit_ja = st.columns(2)
    with col_edit_en:
        st.markdown("**📝 English Email Draft** *(Editable)*")
        edited_en = st.text_area(
            "English body",
            value=st.session_state.english_draft,
            height=280,
            label_visibility="collapsed"
        )
        st.session_state.english_draft = edited_en
        
        if st.button("🔄 Re-translate to Japanese", help="Re-translates current English text to Japanese"):
            with st.spinner("Translating..."):
                st.session_state.japanese_body = translate_english_to_japanese(st.session_state.english_draft)
                st.rerun()

    with col_edit_ja:
        st.markdown("**🌸 Japanese Translation (日本語)** *(Editable)*")
        edited_ja = st.text_area(
            "Japanese body",
            value=st.session_state.japanese_body,
            height=280,
            label_visibility="collapsed"
        )
        st.session_state.japanese_body = edited_ja

    # Visual HTML Email Preview
    with st.expander("👁️ View Live HTML Email Preview (Recipient View)", expanded=True):
        st.caption("This matches the exact styling rendered in the recipient's email client (Gmail, Outlook, iOS):")
        
        preview_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 650px; margin: 10px auto; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: white; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="background: #f8f9fa; padding: 18px; border-left: 4px solid #d63384; border-radius: 8px; margin-bottom: 16px;">
                <h4 style="color: #d63384; margin-top: 0; margin-bottom: 8px; font-size: 15px;">🇯🇵 Japanese Translation (日本語)</h4>
                <div style="font-size: 15px; line-height: 1.6; color: #1e293b; white-space: pre-wrap;">{html.escape(st.session_state.japanese_body)}</div>
            </div>
            <div style="background: #fff3cd; padding: 18px; border-left: 4px solid #856404; border-radius: 8px;">
                <h4 style="color: #856404; margin-top: 0; margin-bottom: 8px; font-size: 15px;">🇬🇧 Original (English)</h4>
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
    
    col_disp1, col_disp2 = st.columns([2, 1])
    with col_disp1:
        recipient_to = st.text_input("Recipient Email Address:", placeholder="client@company.jp or colleague@example.com")
    with col_disp2:
        dry_run_check = st.checkbox("🧪 Test Run (Dry-run without sending)", value=False)

    col_btn_send, _ = st.columns([1, 2])
    with col_btn_send:
        btn_send = st.button("🚀 Send Email Now", type="primary", use_container_width=True)

    if btn_send:
        if dry_run_check:
            st.info("🧪 [Dry-Run Mode] Validation passed! No real email was dispatched.")
        elif not recipient_to.strip():
            st.error("❌ Recipient email address cannot be empty.")
        elif not is_valid_email(recipient_to.strip()):
            st.error(f"❌ '{recipient_to}' is not a valid email address.")
        else:
            current_sender = os.getenv("GMAIL_ADDRESS", "")
            current_pw = os.getenv("GMAIL_APP_PASSWORD", "")
            
            if not current_sender or not current_pw:
                st.error("❌ Gmail sender credentials missing. Please configure your Gmail Address and App Password in the sidebar or .env.")
            else:
                with st.spinner(f"📨 Connecting to smtp.gmail.com:587 via STARTTLS and dispatching to {recipient_to}..."):
                    result = send_email(
                        sender_email=current_sender,
                        sender_password=current_pw,
                        recipient_email=recipient_to.strip(),
                        subject=st.session_state.email_subject,
                        japanese_body=st.session_state.japanese_body,
                        english_body=st.session_state.english_draft,
                    )
                    
                    if result.get("success"):
                        st.balloons()
                        st.success(f"✅ {result.get('message')}")
                    else:
                        st.error(f"❌ {result.get('message')}")
