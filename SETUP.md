# English-to-Japanese Email Translator — Streamlined Setup Guide

> **College Minor Project** | Cloud AI + Google Translate Edition  
> Fast, lightweight, pure-Python architecture fully compatible with **Python 3.10 through 3.14.2**.

---

## 🚀 Quick Highlights: What's New & Streamlined

This project has been completely modernized from a heavy local-inference architecture to a **zero-local-weight, cloud-powered pipeline**.

### ⚡ Old Setup vs. New Streamlined Setup

| Feature / Requirement | ❌ Old Setup (Legacy) | ✅ New Streamlined Setup |
|---|---|---|
| **Python Support** | Restricted to 3.9 – 3.11 | **Universal: Python 3.10 – 3.14.2 supported** |
| **Model Download** | **2.5 GB+** HuggingFace download (`nllb-200-distilled-600M`) | **0 MB** — Instant cloud translation via Google Translate |
| **Hardware & GPU** | Required 8–16 GB RAM + CUDA 11.8/12.1 for acceptable speed | Runs on **any CPU / laptop (< 512 MB RAM)** |
| **C-Extensions & PyTorch** | Required compiling PyTorch wheels (broken on Python 3.14.2) | **Zero PyTorch, zero CUDA, zero C-extensions** |
| **Dependencies** | 7+ heavy libraries (`torch`, `transformers`, `sentencepiece`, etc.) | **Only 3–4 lightweight packages** (`deep-translator`, `python-dotenv`, `requests`) |
| **Hardcoded Paths** | Hardcoded Windows paths (`C:\Users\kumar\...`) | Clean environment variables & native HTTP fallbacks |
| **Setup Time** | 30–60 minutes (model downloads & wheel builds) | **Under 2 minutes** |

> [!IMPORTANT]
> **No Model Downloads or CUDA Required!**  
> You **NO LONGER** need to download multi-gigabyte HuggingFace models, configure CUDA drivers, or hunt down custom PyTorch wheels for Python 3.14.2. Translation runs instantly with Google Translate via `deep-translator` (with automatic standard library `urllib` fallback), and email generation is handled by NVIDIA AI Cloud Endpoints.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Create a Virtual Environment](#3-create-a-virtual-environment)
4. [Install Dependencies](#4-install-dependencies)
5. [Environment Configuration (`.env`)](#5-environment-configuration-env)
   - [NVIDIA API Key Setup](#5a-nvidia-api-key-setup)
   - [Gmail App Password Setup](#5b-gmail-app-password-setup)
6. [Verification & Module Testing](#6-verification--module-testing)
   - [Test 1: Translation Module](#test-1-translation-module)
   - [Test 2: Email Generation Module](#test-2-email-generation-module)
   - [Test 3: Email Sender Module](#test-3-email-sender-module)
   - [Test 4: Full Pipeline End-to-End Test](#test-4-full-pipeline-end-to-end-test)
   - [Test 5: ⚡ Automatic Dry-Run with Sending (`--auto-test`)](#test-5--automatic-dry-run-with-sending---auto-test)
   - [Test 6: 🧪 Manual Dry-Run with Sending (`--manual-test`)](#test-6--manual-dry-run-with-sending---manual-test)
7. [Troubleshooting Guide](#7-troubleshooting-guide)
8. [Project Structure Reference](#8-project-structure-reference)

---

## 1. Prerequisites

Before starting, ensure you have the following installed on your machine:

| Requirement | Supported Version | Notes |
|---|---|---|
| **Python** | **3.10 – 3.14.2** | Verified compatible with the latest Python 3.14.2 ([python.org](https://www.python.org/downloads/)) |
| **pip** | 23.0+ | Standard Python package installer (comes bundled with Python) |
| **Git** | Any modern version | For cloning the project repository ([git-scm.com](https://git-scm.com/)) |
| **OS** | Windows 10/11, macOS, Linux | Cross-platform pure Python |
| **System Memory** | 512 MB+ RAM | Very lightweight memory footprint |
| **Disk Space** | < 50 MB | No multi-gigabyte model weights stored locally |
| **Internet** | Required | For NVIDIA NIM endpoints, Google Translate, and Gmail SMTP |

> [!TIP]
> Verify your Python installation in your terminal:
> ```bash
> python --version
> pip --version
> ```

---

## 2. Clone the Repository

Clone the project to your local directory:

```bash
git clone https://github.com/vkhere/college-minor-project-01.git "email translator"
cd "email translator"
```

*(Or open your existing project root folder in PowerShell, CMD, or Terminal).*

---

## 3. Create a Virtual Environment

Isolate the project dependencies by creating a Python virtual environment:

### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> [!NOTE]
> If PowerShell blocks script execution, run:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run `.\venv\Scripts\Activate.ps1`.

### Windows (Command Prompt)
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```

### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

Once activated, your command line prompt will show `(venv)`.

---

## 4. Install Dependencies

The project requires only **3 to 4 lightweight, pure-Python packages**.

### Option A — Install via `requirements.txt` (Recommended)

```bash
pip install -r requirements.txt
```

#### What's in `requirements.txt`:
```txt
# Core lightweight translation & utilities
deep-translator>=1.11.4
python-dotenv>=1.0.0
requests>=2.31.0

# Optional LangChain orchestration (fallback uses native urllib HTTP)
langchain-core>=0.1.30
langchain-nvidia-ai-endpoints>=0.1.0
```

### Option B — Direct Minimal Installation

If you prefer installing packages directly:

```bash
pip install deep-translator python-dotenv requests
```

> [!TIP]
> **Zero-Dependency Native Fallback:**  
> Both `translate.py` and `write_email.py` include built-in fallbacks to Python's standard library (`urllib.request` and `json`). Even in environments where third-party packages cannot be installed, the core translation and email drafting logic will still function via standard HTTPS calls!

---

## 5. Environment Configuration (`.env`)

The project uses a `.env` file to securely store API keys and email credentials. **Never commit `.env` to Git.**

Create a `.env` file in the root directory of the project:

```ini
# .env — English-to-Japanese Email Translator Credentials

# 1. NVIDIA AI Foundation Endpoints (for write_email.py)
NVIDIA_API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=google/diffusiongemma-26b-a4b-it

# 2. Gmail SMTP Credentials (for email_sender.py)
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

---

### 5a. NVIDIA API Key Setup

`write_email.py` uses NVIDIA AI Foundation Endpoints (NIM) to compose professional corporate emails.

1. Go to [integrate.api.nvidia.com](https://integrate.api.nvidia.com) (or [build.nvidia.com](https://build.nvidia.com)).
2. Sign in or create a free **NVIDIA Developer** account.
3. Browse models (e.g., `google/diffusiongemma-26b-a4b-it` or `meta/llama-3.1-70b-instruct`).
4. Click **Get API Key** or generate one from the API Keys dashboard.
5. Copy your key (starts with `nvapi-...`).
6. Paste it into `.env` as `NVIDIA_API_KEY`.

---

### 5b. Gmail App Password Setup

`email_sender.py` uses Gmail's secure SMTP server (`smtp.gmail.com:587` with TLS). Google requires a **16-character App Password** (your standard Gmail login password will not work).

1. Open your Google Account at [myaccount.google.com](https://myaccount.google.com).
2. Go to the **Security** tab on the left.
3. Under *How you sign in to Google*, ensure **2-Step Verification** is turned **ON**.
4. In the top search bar, type **"App passwords"** and click on it.
5. Enter a name for the app (e.g., `EmailTranslator`) and click **Create**.
6. Google will display a **16-character code** (e.g., `abcd efgh ijkl mnop`).
7. Copy this code, remove spaces (or keep them), and paste it into `.env` as `GMAIL_APP_PASSWORD`.
8. Set `GMAIL_ADDRESS` to your full Gmail address.

> [!CAUTION]
> Treat your App Password like a secret key. Do not share it, and never upload `.env` to GitHub.

---

## 6. Verification & Module Testing

Test each module individually to verify your environment and credentials before running the full pipeline.

### Test 1: Translation Module

Tests Google Translate integration (via `deep-translator` or the native HTTP fallback).

```bash
python email_trans/translate.py
```

**Expected output:**
```
Original English:
 Dear Team,
We are pleased to inform you that the project has been successfully completed.

Translated Japanese:
 チームの皆様、
プロジェクトが無事に完了したことをご報告いたします。
```
*Latency: < 300 ms (no model loading delays!)*

---

### Test 2: Email Generation Module

Tests the NVIDIA NIM API endpoint for drafting a formal corporate email.

```bash
python email_trans/write_email.py
```

**Expected output:**
```
Generating formal email for topic: 'informing client for project completion.'...

--- Generated Email ---

Subject: Project Completion Notice - [Project Name]

Dear [Client Name],

I am writing to formally announce the successful completion of [Project Name]...
```

---

### Test 3: Email Sender Module

Tests the SMTP delivery mechanism with a dual-card bilingual HTML template.

```bash
python email_trans/email_sender.py
```

**Expected output:**
```
Email sent successfully!
```
*(Check your recipient inbox to view the styled Japanese top card and English reference card).*

---

### Test 4: Full Pipeline End-to-End Test

Test the complete chain (Drafting $\rightarrow$ Translation $\rightarrow$ Output) using an inline Python command:

```bash
python -c "from email_trans.write_email import generate_email; from email_trans.translate import translate_english_to_japanese; draft = generate_email('Q3 performance review meeting scheduled for Friday'); ja = translate_english_to_japanese(draft); print('=== ENGLISH DRAFT ===\n', draft); print('\n=== JAPANESE TRANSLATION ===\n', ja)"
```

---

### Test 5: ⚡ Automatic Dry-Run with Sending (`--auto-test`)

Tests the complete pipeline via an autonomous self-test without requiring any pre-configured credentials or personal Gmail accounts.

```bash
python email_trans/main.py --topic "Project update" --auto-test
```

**Key Architectural Capabilities:**
- **100% Automated End-to-End Self-Test:** Runs completely hands-free from topic input to inbox verification.
- **On-the-Fly Dual Inbox Provisioning:** Automatically provisions 2 temporary inboxes in real time (one acting as the sender, one as the recipient).
- **Comprehensive Protocol Verification:** Verifies real SMTP TLS handshake, dual-card MIME rendering (Rose Japanese card + Amber English card), and inbox delivery.
- **Zero Credentials Required:** Requires no `.env` setup, no API keys, and no Gmail App Passwords.

---

### Test 6: 🧪 Manual Dry-Run with Sending (`--manual-test`)

Tests sending from any custom or corporate email address via a disposable test SMTP relay with a live web preview.

```bash
python email_trans/main.py --topic "Project update" --manual-test --from dev@company.com --to client@domain.jp
```

**Key Architectural Capabilities:**
- **Completely Free from Any Specific Mail Provider:** Sender does not need to be a Gmail ID. Use any corporate domain (`dev@company.com`), custom tech domain, Outlook, or Yahoo address.
- **Disposable Test SMTP Relay:** Dispatches across real TLS sockets via a disposable test SMTP relay without needing Gmail App Passwords.
- **Live Web Preview of Delivered Email:** Generates a live web preview URL where evaluators and developers can visually inspect the delivered bilingual email rendered with full HTML styling.

---

## 7. Troubleshooting Guide

### 1. `401 Unauthorized` or `AuthenticationError` (NVIDIA API)
* **Cause:** The `NVIDIA_API_KEY` is missing, expired, or copied with unintended quotes/spaces.
* **Fix:**
  - Verify `.env` exists in the **project root directory** (not inside `email_trans/`).
  - Open `.env` and verify `NVIDIA_API_KEY=nvapi-...` has no leading or trailing spaces.
  - Test your key directly by generating a fresh key at [integrate.api.nvidia.com](https://integrate.api.nvidia.com).

---

### 2. `smtplib.SMTPAuthenticationError: (535, ...)`
* **Cause:** Gmail rejected your credentials. Standard Google account passwords are not allowed for SMTP.
* **Fix:**
  - Ensure **2-Step Verification** is active on your Google account.
  - Re-generate an **App Password** from [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
  - Remove all spaces from the 16-character string in `GMAIL_APP_PASSWORD=abcdefghijklmnop`.
  - Double check that `GMAIL_ADDRESS` matches the account where the App Password was created.
* **Alternative (Zero-Credential Testing):**
  - If you do not have a Gmail account or want to test email transmission without exposing personal credentials, use the provider-independent testing modes:
    - ⚡ `python email_trans/main.py --topic "Project update" --auto-test` (automated self-test with 2 temporary inboxes on the fly)
    - 🧪 `python email_trans/main.py --topic "Project update" --manual-test --from dev@company.com --to client@domain.jp` (test dispatch from any corporate/custom domain via disposable test SMTP relay with live web preview URL)

---

### 3. Google Translate Network Timeout or Rate Limit
* **Cause:** Network firewall, VPN, or transient Google Translate throttle.
* **Fix:**
  - `email_trans/translate.py` automatically falls back from `deep-translator` to standard library HTTP (`translate.googleapis.com`).
  - If using a corporate proxy or VPN, ensure outbound HTTPS to `googleapis.com` is permitted.
  - Wait a few moments and retry; the Google Translate endpoint resets rapidly.

---

### 4. `ModuleNotFoundError: No module named 'dotenv'` or `'deep_translator'`
* **Cause:** Python virtual environment is not activated, or packages were installed in a different Python environment.
* **Fix:**
  - Confirm `(venv)` appears in your terminal prompt.
  - Re-run:
    ```bash
    pip install deep-translator python-dotenv requests
    ```

---

### 5. PowerShell Execution Policy Restriction on Windows
* **Cause:** Windows restricts script execution by default (`Activate.ps1 cannot be loaded`).
* **Fix:**
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\venv\Scripts\Activate.ps1
  ```

---

### 6. Python 3.14.2 Compatibility Warnings
* **Notice:** The streamlined setup was designed specifically to eliminate all C-extension and PyTorch build issues under Python 3.14.2.
* If any package displays a deprecation warning, the project will automatically fall back to native standard library modules without breaking execution.

---

### 7. NVIDIA NIM Cloud Endpoint Timeout (`The read operation timed out`)
* **Symptoms:**
  - The email composition process stalls for 30–60 seconds, followed by:
    ```text
    NVIDIA API Connection Error: <urlopen error The read operation timed out>
    ```
    or `urllib.error.URLError: <urlopen error The read operation timed out>`.
* **Root Cause:**
  - Foundation LLM endpoints on NVIDIA NIM (such as `google/diffusiongemma-26b-a4b-it` or `meta/llama-3.1-70b-instruct`) run on distributed cloud GPU clusters.
  - During server cold starts (allocating GPU worker nodes and loading 26B+ model weights into VRAM) or peak multi-tenant request queuing spikes, inference latency can exceed standard 30-second socket deadlines, resulting in client-side read timeouts.
* **Built-in Resilience Features:**
  - **Relaxed Socket Deadline (60s):** The client connection read timeout is set to 60 seconds, giving remote GPU inference nodes adequate headroom to complete container initialization and model execution.
  - **Automated Exponential Backoff:** The client automatically attempts up to 3 retries with progressive backoff delays ($\Delta t_{\text{wait}} = 2\text{s}, 4\text{s}, 8\text{s}$) to smoothly absorb transient queue congestion.
  - **Token Optimization:** Prompt token overhead and maximum completion limits (`max_tokens: 512`) are constrained to reduce KV-cache prefill and generation latency.
* **Recommended Troubleshooting Steps:**
  1. **Allow Automatic Retries to Complete:** In most cases, the automated retry mechanism successfully receives a response on attempt 2 or 3 as the container completes its warm-up cycle.
  2. **Switch to an Alternative High-Availability Model in `.env`:** If the DiffusionGemma 26B endpoint is experiencing sustained queue congestion, switch `NVIDIA_MODEL` in your `.env` file to a high-throughput alternative:
     ```ini
     # Ultra-fast, high-availability instruction model
     NVIDIA_MODEL=meta/llama-3.1-8b-instruct

     # Or flagship instruction model
     NVIDIA_MODEL=meta/llama-3.1-70b-instruct
     ```
  3. **Check Network Connectivity & VPNs:** Corporate proxies or VPNs performing TLS inspection may terminate long-lived HTTP streaming sockets prematurely. Ensure steady outbound HTTPS access to `https://integrate.api.nvidia.com`.
  4. **Use Direct Translation Mode:** When immediate email dispatch is necessary and LLM drafting is not required, use **"Direct Translation"** mode in the Streamlit web interface (`app.py`), which translates pre-written English drafts via Google Translate without invoking the LLM endpoint.

---

## 8. Project Structure Reference

```
email translator/
├── email_trans/
│   ├── __init__.py           # Package initializer
│   ├── translate.py          # Google Translate engine (deep-translator + HTTP fallback)
│   ├── write_email.py        # NVIDIA NIM cloud LLM email composer
│   └── email_sender.py       # Dual-card HTML SMTP email dispatcher
├── .env                      # API keys & Gmail credentials (DO NOT commit)
├── .env.example              # Template for environment variables
├── .gitignore                # Git exclusions (venv, .env, __pycache__)
├── requirements.txt          # Lightweight dependencies (3-4 packages)
├── README.md                 # High-level project documentation
├── SETUP.md                  # This setup guide
└── RULES.md                  # Architectural guidelines & pure-Python standards
```

---

*For issues or project queries, please consult `RULES.md` or contact the project maintainer.*
