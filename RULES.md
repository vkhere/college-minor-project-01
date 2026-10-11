# Project Rules & Development Guidelines

## Project: English-to-Japanese Email Translator (Cloud AI + Google Translate Edition)
**Target Python Version:** 3.10 – 3.14.2  
**Architecture:** Cloud-Only (NVIDIA AI Endpoints + Google Translate API + SMTP)  
**Repository:** [vkhere/college-minor-project-01](https://github.com/vkhere/college-minor-project-01)  

---

## 1. Project Overview & Architectural Principles

### 1.1 Core Responsibilities
| Module | File | Primary Responsibility | Backing Technology |
|---|---|---|---|
| **Email Drafting** | `email_trans/write_email.py` | Formulates professional English emails from user topics. | NVIDIA AI Foundation Endpoints (`google/diffusiongemma-26b-a4b-it` or `meta/llama-3.1-70b-instruct`) via LangChain / HTTP |
| **Language Translation** | `email_trans/translate.py` | Translates English text and subject lines to Japanese without consuming LLM tokens. | Google Translate via `deep-translator` (with zero-dependency urllib HTTP fallback) |
| **Email Delivery** | `email_trans/email_sender.py` | Sends bilingual emails with responsive dual-card HTML layout. | Python Standard Library (`smtplib` + `email.mime`) |
| **CLI Orchestrator** | `email_trans/main.py` | Provides unified CLI, subject line extraction/translation, and dry-run preview. | Python Standard Library (`argparse`) |

### 1.2 Zero-Local-Weight & Zero-C-Extension Policy
- **No Heavy ML Frameworks:** Neither `torch` nor Hugging Face `transformers` may be introduced into the project. This preserves 100% compatibility with Python 3.14.2 and prevents multi-gigabyte disk usage.
- **No Local Model Files:** Local model directories (`.bin`, `.safetensors`, `.pt`) are strictly prohibited in the codebase and `.gitignore`.
- **API Token Conservation:** LLM calls via NVIDIA API keys are strictly restricted to drafting/composition tasks. **All translation tasks must be routed to Google Translate** to minimize token usage and quota consumption.

---

## 2. Python 3.14.2 Coding Standards

### 2.1 Pure Python & Modern Typing
- Code must adhere to PEP 8 standards.
- Type annotations must be modern and standard (e.g., `str`, `dict[str, Any]`, `Optional[str]`).
- Do not use deprecated modules or syntax removed in Python 3.13 / 3.14 (e.g., `cgi`, legacy `asyncio` constructs, or direct C-API dependencies).

### 2.2 Graceful Fallbacks & High Portability
- Any third-party library call (such as `deep-translator` or `langchain-nvidia-ai-endpoints`) must have a native Python standard library fallback (`urllib.request` / `json`).
- If an environment running Python 3.14.2 lacks wheels for complex packages, the native HTTP fallbacks ensure the entire application functions without error.

---

## 3. Security & Secret Management Rules

### 3.1 Credential Protection
- **Rule SEC-01:** Never commit API keys, email addresses, or passwords to git.
- **Rule SEC-02:** Always read credentials from environment variables via `os.getenv(...)` with `.env` managed by `python-dotenv`.
- **Rule SEC-03:** Gmail authentication **MUST** use an App Password (16 characters, 2-Step Verification required). Never prompt or allow user's standard account password.
- **Rule SEC-04:** `.gitignore` must explicitly include `.env`, `.env.local`, `*.log`, and `__pycache__/`.

### 3.2 Secure Transport
- All SMTP connections must execute over TLS using `server.starttls()` on port 587.
- Direct plaintext SMTP on port 25 is strictly forbidden.
- All outbound HTTPS calls (to NVIDIA Endpoints and Google Translate) must enforce TLS 1.3 certificate validation.

---

## 4. Translation Guidelines (Google Translate)

- **Source & Target Identifiers:** Always use ISO 639-1 language codes: `source="en"`, `target="ja"`.
- **Pre-translation Validation:** Empty or whitespace-only strings must immediately return an empty string without making outbound network requests.
- **Error Resilience:** In case `deep-translator` fails or encounters rate limits, automatically fall back to the direct HTTP endpoint (`translate.googleapis.com`).
- **Formatting Preservation:** Ensure line breaks (`\n`) and bullet points are preserved across translation segments.

---

## 5. LLM Prompting & API Token Rules

- **Prompt Tone:** System messages must enforce a formal, corporate, polite tone (*Keigo*-compatible phrasing).
- **Temperature Setting:** Keep temperature between `0.3` and `0.5` to minimize hallucinations while maintaining natural phrasing.
- **Token Caps:** Cap output at 512 tokens to prevent runaway generations.
- **API Base URL:** Default to `https://integrate.api.nvidia.com/v1/`.

---

## 6. Email Formatting & Rendering Rules

- **Dual-Language Layout:** Every email must be dispatched in `multipart/alternative` format containing:
  1. Plain-text version with clean ASCII dividers for text-only clients.
  2. HTML version featuring:
     - Top Card (Light Grey `#f8f9fa` with Rose Accent `#d63384`): Primary Japanese translation.
     - Bottom Card (Warm Amber `#fff3cd` with Dark Amber Accent `#856404`): Original English reference.
     - Footer: Minimalist disclaimer that translation was automatically generated.
- **Safe HTML:** Avoid external CSS files or JavaScript inside the email body; use inline styles for maximum email client compatibility (Gmail, Outlook, Apple Mail).
- **Bilingual Subject Line:** Email headers must follow the convention defined in Section 7: `【Japanese Subject】 English Subject`.

---

## 7. Japanese Subject Line (*Kenmei* / 件名) Standards & Dispatch Rules

### 7.1 Japanese Corporate Correspondence Etiquette (*Business Mail* / ビジネスメール)
- **Rule SUB-01 (Cultural Demarcation with Brackets):** In Japanese corporate culture, the email subject line (*Kenmei* / 件名) is an essential filtering and triage mechanism. Busy executives, partners, and clients judge the priority and context of an email before opening it. Subject lines must be strictly demarcated using Japanese square brackets / *sumitsukikakko* (隅付き括弧 `【...】`), such as:
  - `【対応完了】` (Action Completed / Issue Resolved)
  - `【ご確認】` or `【ご確認のお願い】` (Confirmation Requested)
  - `【日程調整】` or `【日程変更のお願い】` (Schedule Adjustment Request)
  - `【進捗報告】` (Progress Status Report)
  - `【重要】` (High Importance / Critical Notice)
  - `【共有】` or `【情報共有】` (Information Sharing / FYI)
  - `【件名: ...】` / `【ご連絡】` (Formal Notice Header)
- **Rule SUB-02 (Tone & Conciseness):** Japanese subject lines should favor concise noun-phrase endings (*taigendome* / 体言止め) or formal polite request patterns (*...のご案内*, *...のお願い*), adhering strictly to business *Keigo* principles.

### 7.2 Isolated Extraction, Translation & Side-by-Side Presentation
- **Rule SUB-03 (Isolated Translation):** The English subject line must be extracted independently from the AI-generated draft (via `Subject:` header parsing) or user input. It must be translated as a standalone string via Google Translate (`translate_english_to_japanese`) rather than concatenated into the body, preventing lost punctuation, grammatical merging, or corrupted structural formatting.
- **Rule SUB-04 (Side-by-Side Inspection):** Both the English and Japanese subject lines must be presented side-by-side in user interfaces (e.g., Streamlit review cards) and CLI terminal previews. This allows senders to review, edit, and verify both cultural representations simultaneously before sending.

### 7.3 Canonical Bilingual Dispatch Convention
- **Rule SUB-05 (Bilingual Subject Dispatch Format):** When assembling the MIME `Subject:` header for SMTP transmission, the subject line **MUST** adhere to the standard bilingual convention:
  ```text
  【Japanese Subject】 English Subject
  ```
  *(Examples:)*
  - `【対応完了】 Project Completion Notification`
  - `【日程変更のお願い】 Meeting Reschedule Request`
  - `【進捗のご報告】 Weekly Engineering Status Update`
  - `【ご確認のお願い】 Deliverables Review Request`
- **Rule SUB-06 (Bracket Deduplication):** Ensure no double-bracket artifacts (e.g., `【【...】】`) are introduced if the translated Japanese string or user input already carries bracket punctuation.
- **Rule SUB-07 (Dual-Audience Utility):** This format guarantees immediate comprehension for Japanese recipients in native mobile/desktop notifications, while maintaining seamless searchability and context for international English-speaking stakeholders.
