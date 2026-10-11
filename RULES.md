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
| **Language Translation** | `email_trans/translate.py` | Translates English text to Japanese without consuming LLM tokens. | Google Translate via `deep-translator` (with zero-dependency urllib HTTP fallback) |
| **Email Delivery** | `email_trans/email_sender.py` | Sends bilingual emails with responsive dual-card HTML layout. | Python Standard Library (`smtplib` + `email.mime`) |
| **CLI Orchestrator** | `email_trans/main.py` | Provides unified command-line interface and dry-run preview. | Python Standard Library (`argparse`) |

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
