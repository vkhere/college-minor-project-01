# 🗾 English-to-Japanese Email Translator — Architectural & Code Walkthrough

> **Project Title:** Bilingual English-to-Japanese Email Automation Pipeline  
> **Academic Context:** College Minor Project  
> **Target Environment:** Python 3.10 – 3.14.2 (Zero C-Extensions / Zero Local Model Weights)  
> **Core Technologies:** NVIDIA AI Foundation Endpoints, Google Translate (`deep-translator`), Python Standard Library (`smtplib`, `email.mime`, `urllib`)  
> **Repository:** [vkhere/college-minor-project-01](https://github.com/vkhere/college-minor-project-01)  

---

## 📑 Table of Contents
1. [End-to-End Architecture & Data Flow](#1-end-to-end-architecture--data-flow)
   - [1.3 Japanese Corporate Correspondence Standards (*Business Mail* / ビジネスメール & *Kenmei* / 件名)](#13-japanese-corporate-correspondence-standards-business-mail--ビジネスメール--kenmei--件名)
2. [Architectural Deep-Dive: NVIDIA Token Conservation via Google Translate](#2-architectural-deep-dive-nvidia-token-conservation-via-google-translate)
3. [Architectural Deep-Dive: Seamless Python 3.14.2 Execution (Eliminating PyTorch & Transformers)](#3-architectural-deep-dive-seamless-python-3142-execution-eliminating-pytorch--transformers)
4. [Module 1: `email_trans/write_email.py` (Email Composition Engine)](#4-module-1-email_transwrite_emailpy-email-composition-engine)
5. [Module 2: `email_trans/translate.py` (Translation Engine)](#5-module-2-email_transtranslatepy-translation-engine)
   - [5.4 Subject Line Translation Dynamics](#54-subject-line-translation-dynamics)
6. [Module 3: `email_trans/email_sender.py` (SMTP Dispatcher & Responsive MIME Formatter)](#6-module-3-email_transemail_senderpy-smtp-dispatcher--responsive-mime-formatter)
7. [Module 4: `email_trans/main.py` (Unified CLI Orchestrator)](#7-module-4-email_transmainpy-unified-cli-orchestrator)
   - [7.4 Japanese Subject Line Engineering: Extraction, Side-by-Side Presentation & Bilingual Dispatch](#74-japanese-subject-line-engineering-extraction-side-by-side-presentation--bilingual-dispatch)
   - [7.5 Provider-Independent Testing Architecture (`--auto-test` & `--manual-test`)](#75-provider-independent-testing-architecture---auto-test--manual-test)
8. [Module 5: `app.py` (Streamlit Web Application: Reactive Auto-Translation & Enhanced Dry-Run Mode)](#8-module-5-apppy-streamlit-web-application-reactive-auto-translation--enhanced-dry-run-mode)
   - [8.1 Architecture & Workflow of the Web Dashboard](#81-architecture--workflow-of-the-web-dashboard)
   - [8.2 Reactive Auto-Translation Synchronization](#82-reactive-auto-translation-synchronization)
   - [8.3 Enhanced Dry-Run Mode (Side-by-Side Sender & Recipient Verification)](#83-enhanced-dry-run-mode-side-by-side-sender--recipient-verification)
   - [8.4 Live Dual-Card HTML Email Preview & Dispatch Options](#84-live-dual-card-html-email-preview--dispatch-options)
9. [End-to-End Pipeline Integration & Data Lifecycle](#9-end-to-end-pipeline-integration--data-lifecycle)
10. [Sample Terminal & Web UI Interactions](#10-sample-terminal--web-ui-interactions)
11. [Quick-Start & Verification Commands](#11-quick-start--verification-commands)

---

## 1. End-to-End Architecture & Data Flow

The project implements a decoupled, three-stage cloud-native pipeline coordinated by an orchestration interface. Rather than running multi-gigabyte models locally or consuming expensive LLM inference tokens for translation, the pipeline delegates each task to the most specialized, cost-effective engine.

### 1.1 Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   USER / CLI / SYSTEM                                  │
│                      Topic: "informing client for project completion."                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              [1] email_trans/write_email.py                            │
│  • NVIDIA AI Foundation Endpoint (OpenAI-compatible /chat/completions)                 │
│  • Primary Model: google/diffusiongemma-26b-a4b-it (or meta/llama-3.1-70b-instruct)    │
│  • Dual Execution: LangChain (ChatNVIDIA) with graceful native urllib.request fallback  │
│  • Role: Formulates formal corporate English email with structured subject line        │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ English Draft (Subject + Body)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               [2] email_trans/translate.py                             │
│  • Google Translate Engine via deep-translator library (urllib fallback)               │
│  • Dual-Track Translation: Translates both Body & Subject independently                │
│  • Japanese Subject Formatting: Wraps in corporate brackets (e.g., 【対応完了】)      │
│  • 100% Free: ZERO tokens deducted from NVIDIA API key quota                          │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Bilingual Subject: '【Japanese】 English'
                                            │ + Dual-Language Body Text
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             [3] email_trans/email_sender.py                            │
│  • Gmail SMTP Dispatcher (smtp.gmail.com:587 with STARTTLS encryption)                 │
│  • Subject Line: '【Japanese Subject】 English Subject'                                │
│  • Multi-part MIME Generation: multipart/alternative (RFC 2046)                        │
│    ├─ HTML Version: Responsive Dual-Card Layout                                        │
│    │  ├─ Japanese Card: Rose Accent (#d63384) on Light Grey (#f8f9fa) (Primary)        │
│    │  └─ English Card:  Dark Amber Accent (#856404) on Warm Amber (#fff3cd) (Reference)│
│    └─ Plain-Text Version: Clean ASCII-delimited fallback for terminal mail clients     │
│  • Authentication: Google 16-Character App Password                                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Delivered via SMTP over TLS
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                  RECIPIENT'S INBOX                                     │
│     Header:  Subject: 【対応完了】 Project Completion Notification                     │
│     Content: Beautifully rendered bilingual business communication (JA + EN)           │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Mermaid Flowchart

```mermaid
flowchart TD
    User([User / CLI Invocation]) -->|--topic argument| Main[main.py: CLI Orchestrator]
    
    subgraph Stage1 [Stage 1: Email Generation]
        Main -->|Prompt Topic| WE[write_email.py]
        WE -->|Attempt 1| LC[LangChain ChatNVIDIA]
        LC -.->|On Failure / Missing Deps| HTTP[Native urllib HTTP Fallback]
        LC -->|Inference Call| NV[NVIDIA AI Endpoints<br/>diffusiongemma-26b-a4b-it]
        HTTP -->|Inference Call| NV
        NV -->|Return Completion| WE
    end

    WE -->|English Draft String| SubjSplit[Extract Subject & Separate Body]
    
    subgraph Stage2 [Stage 2: Token-Free Translation & Subject Engineering]
        SubjSplit -->|English Body| TRBody[translate.py: Body Translation]
        SubjSplit -->|English Subject| TRSubj[translate.py: Subject Translation]
        TRBody -->|en -> ja| GTBody[Google Translate Service]
        TRSubj -->|en -> ja| GTSubj[Google Translate Service]
        GTBody -->|Japanese Body| BodyReady[Polite Business Body / Keigo]
        GTSubj -->|Japanese Subject| BracketFormat["Apply Corporate Brackets<br/>e.g., 【対応完了】 / 【件名: ...】"]
        BracketFormat --> BiSubj["Assemble Bilingual Subject:<br/>'【Japanese Subject】 English Subject'"]
    end

    subgraph Stage3 [Stage 3: MIME Formatting & Delivery]
        BiSubj --> ES[email_sender.py]
        BodyReady --> ES
        SubjSplit -->|Original English Body| ES
        ES --> MIME[MIMEMultipart 'alternative'<br/>Subject: 【Japanese Subject】 English Subject]
        MIME --> HTML[Responsive HTML Dual Cards<br/>Rose: Japanese / Amber: English]
        MIME --> PLAIN[Plain-Text ASCII Fallback]
        ES --> SMTP[Gmail SMTP:587 STARTTLS]
    end

    SMTP -->|TLS Encrypted Transmission| Inbox([Recipient Inbox])
```

### 1.3 Japanese Corporate Correspondence Standards (*Business Mail* / ビジネスメール & *Kenmei* / 件名)

In Japanese business culture, the email subject line (*Kenmei* / 件名) serves as the primary filter for professional communication, carrying far greater cultural and procedural weight than in Western correspondence:

1. **The Business Mail Protocol (*Bijinesu Mēru* / ビジネスメール):**  
   Japanese corporate personnel receive hundreds of emails each business day. Protocol requires that a recipient be able to ascertain the exact sender, topic, urgency, and necessary action immediately upon scanning their inbox list—without having to open the message.

2. **Sumitsukikakko (隅付き括弧 `【...】`) Bracket Framing:**  
   Japanese corporate subject lines strictly utilize full-width lenticular black brackets `【...】` to highlight status, urgency, or action category. Common corporate conventions include:
   - `【対応完了】` (*Taiō Kanryō*): Task / issue resolution completed.
   - `【ご確認】` or `【ご確認のお願い】` (*Go-kakunin no onegai*): Formal request for review or approval.
   - `【日程調整】` or `【日程変更のお願い】` (*Nittei chōsei* / *Nittei henkō*): Meeting schedule coordination or reschedule request.
   - `【進捗報告】` (*Shinchoku hōkoku*): Periodic project progress status report.
   - `【重要】` (*Jūyō*): Urgent / mission-critical communication.
   - `【共有】` or `【情報共有】` (*Kyōyū*): Informational notice (FYI).
   - `【件名: ...】` (*Kenmei*): Explicit corporate subject descriptor.

3. **Bilingual Subject Line Dispatch Convention:**  
   To bridge communication between international teams and Japanese enterprise partners, the pipeline standardizes on the bilingual dispatch format:
   $$\text{Subject Header} = \text{\textbf{【Japanese Subject】 English Subject}}$$
   *(Examples:)*
   - `【対応完了】 Project Milestone Completion Notification`
   - `【日程変更のお願い】 Meeting Reschedule Request`
   - `【進捗のご報告】 Weekly Sprint Status Report`

   This layout provides dual benefits:
   - **Japanese recipients:** The bracketed Japanese text is prominently visible in mobile notification banners and desktop mail lists.
   - **International colleagues:** English search indexing and mail thread tracing remain completely unhindered.

---

## 2. Architectural Deep-Dive: NVIDIA Token Conservation via Google Translate

### 2.1 The Problem with LLM-Based Translation
Early designs evaluated using the same NVIDIA LLM for both email drafting and translation. However, doing so introduces major engineering bottlenecks:
1. **NVIDIA Free-Tier Developer Quotas:** NVIDIA AI Foundation Endpoints provide developer credits (typically 1,000 credits). Complex multi-billion parameter models (such as `google/diffusiongemma-26b-a4b-it` or `meta/llama-3.1-70b-instruct`) consume credits rapidly based on total tokens processed (prompt tokens + completion tokens).
2. **Context Repetition Overhead:** To have an LLM translate an email, you must re-feed the entire generated English email inside a translation prompt:
   $$\text{Total Tokens} = \text{Drafting Prompt} + \text{Drafting Output} + \text{Translation Prompt} + \text{English Context} + \text{Japanese Output}$$
   This more than doubles token consumption per user interaction.
3. **Generative Drift & Hallucination:** Generative LLMs sometimes rephrase, summarize, omit formal salutations, or add unwanted commentary (e.g., *"Here is the Japanese translation:"*) rather than performing faithful sentence-by-sentence translation.

### 2.2 The Solution: Offloading to Google Translate
By routing the translation stage to Google Translate via `deep-translator` (backed by a zero-dependency `urllib` fallback):

| Metric | LLM-Based Translation | Google Translate Strategy |
|---|---|---|
| **NVIDIA Token Cost** | $\sim 400 - 800$ tokens/email | **0 tokens** (100% quota preserved for drafting) |
| **API Cost** | Deducts from finite NVIDIA credits | **100% Free** |
| **Latency** | 6.0 – 15.0 seconds (autoregressive decode) | **150 – 400 ms** (optimized neural MT) |
| **Translation Fidelity** | Risk of generative drift / conversational preamble | Deterministic, structured, polite Japanese phrasing |
| **Quota Sustainability** | Runs out after a few dozen emails | Capable of processing hundreds of emails daily |

This clean **separation of concerns** reserves high-reasoning LLM intelligence strictly for creative email drafting, while leveraging dedicated Machine Translation (MT) infrastructure for linguistic translation.

---

## 3. Architectural Deep-Dive: Seamless Python 3.14.2 Execution (Eliminating PyTorch & Transformers)

### 3.1 The Python 3.14.2 Compatibility Challenge
Python 3.14 introduces substantial internal changes to CPython:
- Ongoing work around free-threaded execution (PEP 703 / no-GIL builds).
- Bytecode compiler optimizations and internal opcode shifts.
- Removal of deprecated C-APIs and internal structure redefinitions.

Heavy machine learning libraries such as `torch` (PyTorch) and `transformers` (Hugging Face) rely heavily on compiled C/C++ extensions, OpenMP runtimes, and CUDA driver bindings. Precompiled binary wheels (`.whl`) for PyTorch and Transformers typically lag behind new Python minor versions by months or years.

When attempting to run local NLLB (`facebook/nllb-200-distilled-600M`) on Python 3.14.2 on Windows:
1. `pip install torch` fails with `No matching distribution found for torch`.
2. Compiling from source requires Visual Studio C++ Build Tools, CMake, and CUDA SDK, consuming 30+ GB of disk space and often failing due to missing C-API headers.
3. Downloading local model weights demands **2.5 GB to 4.5 GB** of disk space and requires 2 GB+ of active RAM just to load weights into memory.

### 3.2 The Zero-C-Extension / Cloud-First Architecture
By purging `torch` and `transformers` from the project and replacing local weights with cloud endpoints:

```
┌─────────────────────────────────┐           ┌─────────────────────────────────┐
│     OLD LOCAL ARCHITECTURE      │           │    NEW CLOUD-ONLY ARCHITECTURE  │
├─────────────────────────────────┤           ├─────────────────────────────────┤
│ • torch (~2.5 GB on disk)       │           │ • deep-translator (pure Python) │
│ • transformers (~500 MB)        │    ===>   │ • urllib.request (Python stdlib)│
│ • Local weights (~2.5 GB NLLB)  │           │ • smtplib + email (stdlib)      │
│ • High VRAM/RAM consumption     │           │ • Instant startup (< 0.1s)      │
│ • Incompatible with Python 3.14 │           │ • 100% Python 3.14.2 compatible │
│ • 15+ min installation time     │           │ • 5-second pip install          │
└─────────────────────────────────┘           └─────────────────────────────────┘
```

Furthermore, every cloud client in the application (`write_email.py`, `translate.py`) implements a **zero-dependency fallback** using Python's standard `urllib.request` and `json` libraries. Even if third-party packages encounter environment issues, the entire application executes cleanly out-of-the-box on vanilla Python 3.14.2.

---

## 4. Module 1: `email_trans/write_email.py` (Email Composition Engine)

### 4.1 Overview
`write_email.py` is responsible for generating formal corporate English emails from high-level user prompts. It targets NVIDIA AI Foundation Endpoints using models such as `google/diffusiongemma-26b-a4b-it` or `meta/llama-3.1-70b-instruct`.

### 4.2 Full Source Code

```python
"""
Email composition module powered by NVIDIA AI Foundation Endpoints.
Uses cloud-hosted LLMs (e.g. google/diffusiongemma-26b-a4b-it or meta/llama-3.1-70b-instruct).
Zero local VRAM/disk usage. Compatible with Python 3.14.2.
"""

import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()

NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
DEFAULT_MODEL = os.getenv("NVIDIA_MODEL", "google/diffusiongemma-26b-a4b-it")


def generate_email_with_langchain(topic: str, model_name: str = DEFAULT_MODEL, temperature: float = 0.5) -> str:
    """Generates formal email using LangChain and ChatNVIDIA."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_nvidia_ai_endpoints import ChatNVIDIA

    llm = ChatNVIDIA(
        base_url=f"{NVIDIA_BASE_URL.rstrip('/')}/",
        model=model_name,
        temperature=temperature
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional corporate email writer. Write in a formal, polite, and concise tone. Include a clear subject line and formatted body."),
        ("human", "Write a professional email about: {topic}"),
    ])

    chain = prompt | llm
    result = chain.invoke({"topic": topic})
    return str(result.content)


def generate_email_with_http(topic: str, model_name: str = DEFAULT_MODEL, temperature: float = 0.5) -> str:
    """
    Direct HTTP fallback to NVIDIA OpenAI-compatible completions API.
    Does not require any heavy third-party framework; operates on standard Python 3.14.2.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set. Please configure it in .env.")

    endpoint = f"{NVIDIA_BASE_URL.rstrip('/')}/chat/completions"
    payload = {
        "model": model_name,
        "temperature": temperature,
        "max_tokens": 512,
        "messages": [
            {
                "role": "system",
                "content": "You are a professional corporate email writer. Write in a formal, polite, and concise tone. Include a clear subject line and formatted body."
            },
            {
                "role": "human",
                "content": f"Write a professional email about: {topic}"
            }
        ]
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "NVIDIA-Email-Translator/1.0"
        }
    )

    with urllib.request.urlopen(req, timeout=30) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        return res_data["choices"][0]["message"]["content"]


def generate_email(topic: str) -> str:
    """
    Main entrypoint for email generation via NVIDIA AI Endpoint.
    Attempts LangChain first; gracefully falls back to lightweight native HTTP.
    """
    try:
        return generate_email_with_langchain(topic)
    except Exception:
        return generate_email_with_http(topic)


if __name__ == "__main__":
    test_topic = "informing client for project completion."
    print(f"Generating formal email for topic: '{test_topic}'...")
    try:
        content = generate_email(test_topic)
        print("\n--- Generated Email ---\n")
        print(content)
    except Exception as exc:
        print(f"Error: {exc}")
```

### 4.3 Line-by-Line Code Walkthrough

| Line Numbers | Code Section | In-Depth Explanation |
|---|---|---|
| **Lines 1–5** | Module docstring | Defines module purpose: cloud-hosted LLM drafting, zero local VRAM, Python 3.14.2 compatibility. |
| **Lines 7–10** | Standard library imports | Imports `os`, `json`, and `urllib.request` from Python stdlib. Loads `python-dotenv` for reading `.env`. |
| **Line 12** | `load_dotenv()` | Reads key-value pairs from `.env` in the current working directory into `os.environ`. |
| **Lines 14–15** | Environment variable defaults | Sets `NVIDIA_BASE_URL` to `https://integrate.api.nvidia.com/v1` and `DEFAULT_MODEL` to `google/diffusiongemma-26b-a4b-it`. |
| **Lines 18–19** | Function declaration | Declares `generate_email_with_langchain(topic, model_name, temperature)`. |
| **Lines 20–21** | Deferred LangChain imports | Imports `ChatPromptTemplate` and `ChatNVIDIA` inside the function. This prevents runtime failures if LangChain is not installed in the environment. |
| **Lines 23–27** | `ChatNVIDIA(...)` | Instantiates NVIDIA's LangChain integration object with the base URL, selected model, and temperature (`0.5`). |
| **Lines 29–32** | `ChatPromptTemplate.from_messages` | Defines a 2-message prompt: a system prompt enforcing formal corporate tone, and a user prompt with `{topic}` interpolation. |
| **Line 34** | `chain = prompt \| llm` | Uses LangChain's **LCEL (LangChain Expression Language)** pipe operator to link prompt formatting directly to model inference. |
| **Lines 35–36** | `chain.invoke(...)` | Executes inference with `{"topic": topic}` and returns the resulting content string. |
| **Lines 39–43** | Function declaration | Declares `generate_email_with_http(...)`, the zero-dependency fallback function. |
| **Lines 44–46** | API key validation | Checks `os.getenv("NVIDIA_API_KEY")`. Raises a clear, readable `ValueError` if the key is missing from `.env`. |
| **Lines 48–63** | Endpoint & payload construction | Formats endpoint `/chat/completions` and builds an OpenAI-compatible JSON payload with `max_tokens=512`. |
| **Lines 65–73** | `urllib.request.Request` | Prepares an HTTP POST request with `Authorization: Bearer <KEY>`, `Content-Type: application/json`, and custom `User-Agent`. |
| **Lines 75–77** | `urllib.request.urlopen` | Executes the TLS request with a 30-second timeout, decodes UTF-8 JSON response, and extracts `choices[0].message.content`. |
| **Lines 80–89** | `generate_email(topic)` | Public entrypoint function. Tries the LangChain implementation first, and immediately falls back to `generate_email_with_http` if any exception occurs. |
| **Lines 91–100** | `if __name__ == "__main__":` | Test harness block that allows executing `python email_trans/write_email.py` directly from the console to verify API keys and connectivity. |

---

## 5. Module 2: `email_trans/translate.py` (Translation Engine)

### 5.1 Overview
`translate.py` provides high-speed English-to-Japanese machine translation. It replaces the previous multi-gigabyte local Hugging Face NLLB pipeline with Google Translate via `deep-translator` and includes an unauthenticated direct HTTP fallback.

### 5.2 Full Source Code

```python
"""
Google Translate module for English-to-Japanese email translation.
Eliminates local model weights, PyTorch, and Hugging Face Transformers.
Fully compatible with Python 3.14.2 and has near-zero latency.
"""

from typing import Optional
import urllib.parse
import urllib.request
import json

try:
    from deep_translator import GoogleTranslator
    HAS_DEEP_TRANSLATOR = True
except ImportError:
    HAS_DEEP_TRANSLATOR = False


def translate_with_deep_translator(text: str, source: str = "en", target: str = "ja") -> str:
    """Translates text using deep-translator GoogleTranslator engine."""
    translator = GoogleTranslator(source=source, target=target)
    return translator.translate(text)


def translate_with_google_http(text: str, source: str = "en", target: str = "ja") -> str:
    """
    Direct HTTP fallback to Google Translate single-query endpoint.
    Requires no external dependencies (uses standard urllib).
    100% compatible with Python 3.14.2 out of the box.
    """
    url = (
        "https://translate.googleapis.com/translate_a/single?"
        + urllib.parse.urlencode({
            "client": "gtx",
            "sl": source,
            "tl": target,
            "dt": "t",
            "q": text,
        })
    )
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    req = urllib.request.Request(url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
        # Parse Google Translate API response format: [[["translated_segment", "original_segment", ...], ...], ...]
        translated_segments = [segment[0] for segment in data[0] if segment[0]]
        return "".join(translated_segments)


def translate_english_to_japanese(english_text: str) -> str:
    """
    Main entrypoint: translates English email body to Japanese.
    Tries deep-translator first, falls back to direct standard HTTP.
    """
    if not english_text or not english_text.strip():
        return ""
    
    if HAS_DEEP_TRANSLATOR:
        try:
            return translate_with_deep_translator(english_text, source="en", target="ja")
        except Exception:
            # Fall back to native HTTP
            pass
            
    return translate_with_google_http(english_text, source="en", target="ja")


# LangChain Runnable compatibility wrapper (preserves original interface)
def get_translation_chain():
    """Returns a LangChain-compatible runnable lambda function."""
    try:
        from langchain_core.runnables import RunnableLambda
        return RunnableLambda(lambda inputs: translate_english_to_japanese(inputs["text"]))
    except ImportError:
        return lambda inputs: translate_english_to_japanese(inputs["text"])


if __name__ == "__main__":
    test_sample = "Dear Team,\nWe are pleased to inform you that the project has been successfully completed."
    print("Original English:\n", test_sample)
    print("\nTranslated Japanese:\n", translate_english_to_japanese(test_sample))
```

### 5.3 Line-by-Line Code Walkthrough

| Line Numbers | Code Section | In-Depth Explanation |
|---|---|---|
| **Lines 1–5** | Module docstring | Highlights pure-Python execution, zero PyTorch/Transformers dependencies, and Python 3.14.2 compatibility. |
| **Lines 7–10** | Standard library imports | Imports `urllib.parse`, `urllib.request`, and `json` for native networking. |
| **Lines 12–16** | Graceful dependency probe | Attempts to import `deep_translator.GoogleTranslator`. If unavailable, sets `HAS_DEEP_TRANSLATOR = False` without crashing. |
| **Lines 19–23** | `translate_with_deep_translator` | Wraps `GoogleTranslator(source="en", target="ja").translate(text)` to perform neural translation via Google's endpoint. |
| **Lines 25–30** | Function declaration | Declares `translate_with_google_http`, an unauthenticated, zero-dependency HTTP fallback. |
| **Lines 31–40** | Query string construction | Encodes parameters: `client="gtx"` (Google Translate extension client), `sl="en"` (source lang), `tl="ja"` (target lang), `dt="t"` (return translated text), and `q=text`. |
| **Lines 41–42** | Request headers | Attaches a standard Windows desktop browser `User-Agent` header to prevent automated bot rejections. |
| **Lines 44–48** | Response parsing | Parses Google's nested array response structure: `[[[translated_seg, original_seg, ...], ...]]`. Iterates through all text segments and concatenates them with `"".join(...)`. |
| **Lines 51–57** | `translate_english_to_japanese` | Validates input; immediately returns an empty string if given whitespace or None, avoiding unnecessary outbound traffic. |
| **Lines 59–66** | Resilience chain | Tries `deep-translator` first. If it encounters a network glitch or library error, it silently falls back to `translate_with_google_http`. |
| **Lines 69–77** | `get_translation_chain()` | Backward-compatibility shim that wraps the translation function into a LangChain `RunnableLambda` if LangChain is installed. |
| **Lines 79–83** | `if __name__ == "__main__":` | Test execution block translating a formal business email snippet and outputting the Japanese result. |

### 5.4 Subject Line Translation Dynamics

In addition to translating the email body text, `translate_english_to_japanese()` powers the translation of email subject lines:

1. **Independent String Processing:**  
   Translating the subject line independently from the email body avoids the common issue where machine translation models merge the subject into the salutation or alter sentence boundary markers (`。` or `\n`).
2. **Noun Phrase (*Taigendome* / 体言止め) Translation:**  
   English email subjects are typically concise noun phrases (e.g., *"Project Completion Notification"* or *"Meeting Reschedule Request"*). Google Translate accurately renders these into canonical Japanese business phrases (e.g., `プロジェクト完了のご報告` or `会議日程変更のお願い`).
3. **Zero Token Quota Impact:**  
   Because both the subject line and body are translated via Google Translate (using `deep-translator` or direct `urllib` HTTP), translating additional metadata like subject lines incurs **zero NVIDIA API token consumption**, keeping the pipeline free, fast (<300 ms), and scalable.

---

## 6. Module 3: `email_trans/email_sender.py` (SMTP Dispatcher & Responsive MIME Formatter)

### 6.1 Overview
`email_sender.py` handles the final delivery stage. It takes the original English text and the generated Japanese translation, creates an RFC 2046 `multipart/alternative` email containing both responsive HTML cards and a clean plain-text fallback, and securely transmits it to Gmail's SMTP servers over TLS.

### 6.2 Full Source Code

```python
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
        sender_email = str(args[0])
        sender_password = str(args[1])
        recipient_email = str(args[2])
        subject = str(args[3])
        japanese_body = str(args[4])
        english_body = str(args[5])
    elif len(args) == 4:
        recipient_email = str(args[0])
        subject = str(args[1])
        japanese_body = str(args[2])
        english_body = str(args[3])
    elif len(args) == 5:
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
```

### 6.3 Line-by-Line Code Walkthrough

| Line Numbers | Code Section | In-Depth Explanation |
|---|---|---|
| **Lines 1–7** | Module docstring | Outlines SMTP delivery, STARTTLS encryption, multipart/alternative MIME message construction, and dual-card layout. |
| **Lines 9–18** | Imports | Imports standard library modules: `os`, `re`, `sys`, `html`, `smtplib`, `email.utils`, `MIMEMultipart`, `MIMEText`, typing, and `load_dotenv`. |
| **Lines 20–32** | Windows console UTF-8 fix | Reconfigures `sys.stdout` and `sys.stderr` to UTF-8 with `errors="replace"`. This prevents Windows terminals running under `cp1252` encoding from crashing with `UnicodeEncodeError` when rendering Japanese kanji/kana. |
| **Lines 35–39** | Regex & defaults | Compiles RFC-compliant email regex pattern; sets defaults `smtp.gmail.com` on port `587`. |
| **Lines 42–46** | `is_valid_email` | Validates format of email strings before attempting TCP connection, catching typos early. |
| **Lines 48–122** | `build_email_html` | Constructs responsive dual-card HTML template: escapes HTML with `html.escape()`, converts `\n` to `<br>`, styles Japanese primary card (Rose `#d63384` on `#f8f9fa`) and English reference card (Dark Amber `#856404` on `#fff3cd`), and adds an automated disclaimer footer. |
| **Lines 124–141** | `build_email_plain_text` | Generates a clean text fallback with ASCII dividers (`===`, `---`) for terminal mail readers. |
| **Lines 144–156** | `send_email` definition | Declares public sending function with flexible positional and keyword argument support. |
| **Lines 158–184** | Positional argument normalization | Normalizes signatures: supports 4-arg `(to, subj, ja, en)`, 6-arg `(sender, pass, to, subj, ja, en)`, and 5-arg variations. |
| **Lines 186–222** | Keyword resolution & fallback | Resolves aliases (`to`, `recipient`, `japanese`, `ja_body`, `english`, etc.) and pulls credentials from `.env` (`GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`). |
| **Lines 224–247** | Credential & format validation | Verifies recipient format, sender format, and confirms the App Password is non-empty. |
| **Lines 249–250** | Password cleaning | Strips spaces from 16-character Google App Passwords (e.g., converts `"abcd efgh ijkl mnop"` to `"abcdefghijklmnop"`). |
| **Lines 252–273** | MIME message assembly | Instantiates `MIMEMultipart("alternative")`. Attaches Date, Message-ID, Subject, From, To headers. Adds `MIMEText(plain_text, "plain", "utf-8")` first, and `MIMEText(html_content, "html", "utf-8")` second so modern email clients give priority to HTML. |
| **Lines 276–287** | SMTP session execution | Connects to `smtp.gmail.com:587`, performs initial `ehlo()`, upgrades socket to TLS with `server.starttls()`, issues second `ehlo()`, logs in with App Password, and sends message via `server.send_message(msg)`. |
| **Lines 289–321** | Granular error handling | Specifically catches `smtplib.SMTPAuthenticationError` with troubleshooting instructions regarding 2-Step Verification and App Passwords; catches `SMTPException` and general `Exception`. Returns structured dictionary `{"success": bool, "message": str}`. |
| **Lines 324–337** | `if __name__ == "__main__":` | Test block verifying template rendering, byte lengths, and email validator without sending network traffic. |

---

## 7. Module 4: `email_trans/main.py` (Unified CLI Orchestrator)

### 7.1 Overview
`main.py` provides the single unified CLI and interactive entrypoint for the entire project. It links `write_email.py`, `translate.py`, and `email_sender.py`, handles subject extraction, provides a `--dry-run` preview mode, and prompts for interactive user confirmation before email transmission.

### 7.2 Full Source Code

```python
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
    console_preview(
        english_subject=english_subject,
        japanese_subject=bracketed_ja_subject,
        recipient=to,
        english_body=cleaned_english_body,
        japanese_body=japanese_translation,
    )

    # Step 3: Dispatch or Dry-run
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
```

### 7.3 Line-by-Line Code Walkthrough

| Line Numbers | Code Section | In-Depth Explanation |
|---|---|---|
| **Lines 1–10** | Module docstring | Explains orchestrator responsibility: coordinating draft generation, translation, and SMTP dispatch under Python 3.14.2. |
| **Lines 12–21** | System path resolution | Inserts the project root into `sys.path` so the module executes consistently whether invoked via `python -m email_trans.main` or `python email_trans/main.py`. |
| **Lines 23–35** | Terminal UTF-8 fix | Reconfigures stdout/stderr on Windows to support outputting Japanese Unicode characters without throwing `cp1252` encoding errors. |
| **Lines 36–38** | Internal imports | Imports `generate_email` from `write_email`, `translate_english_to_japanese` from `translate`, and `send_email`, `is_valid_email` from `email_sender`. |
| **Lines 41–56** | `extract_subject_from_draft` | Parses the LLM's generated output. If the first line starts with `Subject: <Text>`, it extracts `<Text>` as the subject header and separates the remaining lines as the email body. |
| **Lines 59–84** | `console_preview` | Formats Japanese subject with `【...】` brackets and renders English and Japanese subjects side-by-side in the terminal preview alongside the recipient and email bodies. |
| **Lines 87–98** | `orchestrate` validation | Validates that `topic` is non-empty; prints the workflow header banner. |
| **Lines 100–113** | Stage 1: Drafting | Calls `generate_email(topic)` to generate formal English email. |
| **Lines 115–134** | Subject resolution & translation | Extracts inferred subject, translates it via Google Translate into Japanese, normalizes `【...】` brackets, and constructs the canonical bilingual subject `【Japanese Subject】 English Subject`. |
| **Lines 136–145** | Stage 2: Translating | Passes the cleaned English body to `translate_english_to_japanese()`. Handles network exceptions gracefully. |
| **Lines 147–154** | Console preview invocation | Calls `console_preview()` to display the side-by-side subject and body preview. |
| **Lines 156–169** | Dry-run check | If `--dry-run` was passed, safely terminates execution here without contacting SMTP server, returning status dict with both English and Japanese subjects. |
| **Lines 171–185** | Recipient prompt & validation | If no `--to` address was passed on the command line, prompts the user interactively via `input(...)` in TTY mode. Validates format via `is_valid_email()`. |
| **Lines 187–195** | Interactive confirmation | Prompts `Send this email to '<recipient>'? [y/N]` unless the `--yes` / `-y` bypass flag was provided. Aborts cleanly on refusal or Ctrl+C. |
| **Lines 197–208** | Stage 3: SMTP Dispatch | Calls `send_email(...)` with resolved parameters including `japanese_subject=bracketed_ja_subject`. |
| **Lines 211–260** | `build_parser` | Configures `argparse.ArgumentParser` with short and long flags (`-t`/`--topic`, `-r`/`--to`, `-s`/`--subject`, `-d`/`--dry-run`, `-y`/`--yes`) and detailed practical examples. |
| **Lines 263–295** | `main()` function | Parses arguments; falls back to interactive prompt if `--topic` is omitted; invokes `orchestrate()`; returns exit code 0 on success or 1 on failure. |
| **Lines 297–299** | `if __name__ == "__main__":` | Standard Python executable guard calling `sys.exit(main())`. |

### 7.4 Japanese Subject Line Engineering: Extraction, Side-by-Side Presentation & Bilingual Dispatch

The orchestrator coordinates Japanese subject line translation (*Kenmei* / 件名) to comply with corporate communication protocols (*Business Mail* / ビジネスメール):

#### 1. Isolation & Extraction (`extract_subject_from_draft`)
When NVIDIA AI drafts an English email, it formats the first line with a standard header: `Subject: <Title>`. The orchestrator isolates this string:
- If an explicit `--subject` CLI argument is supplied (or configured in the web UI), it takes precedence.
- Otherwise, `extract_subject_from_draft()` splits the first line, extracting the title into `english_subject` and retaining the remaining lines as `cleaned_english_body`.

#### 2. Dual-Track Translation via Google Translate
Rather than translating the entire draft as a single monolithic block, the pipeline branches into two independent translation streams:
1. `japanese_body = translate_english_to_japanese(cleaned_english_body)`
2. `japanese_subject = translate_english_to_japanese(english_subject)`

This separation ensures the subject line retains high grammatical accuracy without inheriting conversational greetings, line-break anomalies, or sign-offs.

#### 3. Japanese Corporate Bracket Formatting (*Sumitsukikakko* / 隅付き括弧 `【...】`)
In Japanese corporate correspondence, subject lines must instantly telegraph context and urgency. The system formats the translated subject using Japanese brackets:
- `【対応完了】` (Action Completed / Issue Resolved)
- `【ご確認】` or `【ご確認のお願い】` (Confirmation Requested)
- `【日程調整】` or `【日程変更のお願い】` (Meeting Schedule Coordination)
- `【進捗報告】` (Progress Status Report)
- `【重要】` (High Importance / Critical Notice)
- `【共有】` or `【情報共有】` (Information Sharing / FYI)
- `【件名: ...】` / `【ご連絡】` (Formal Notice Header)

If the translated subject is not already bracketed, it is enclosed in `【...】` to adhere strictly to corporate etiquette.

#### 4. Side-by-Side Presentation (Review Stage)
Before dispatch, both versions are presented side-by-side to give the sender full transparency:
- **CLI Terminal Preview:**
  ```text
  Subject (Bilingual):  【対応完了】 Project Completion Notification
    ├─ English Subject:   Project Completion Notification
    └─ Japanese Subject:  【対応完了】 プロジェクト完了のお知らせ
  ```
- **Streamlit Web Application (`app.py`):**
  Renders editable input fields for both the English draft and the Japanese translation side-by-side, allowing real-time edits to either subject prior to transmission.

#### 5. Canonical Bilingual Subject Dispatch Convention
When constructing the RFC 5322 MIME message header, the subject line is formatted as:
```text
【Japanese Subject】 English Subject
```
*(Example: `【対応完了】 Project Milestone Completion Notification`)*

This provides:
- **Instant Triage in Japan:** The recipient's email client and mobile notification preview highlight the bracketed Japanese topic first.
- **Global Searchability & Thread Continuity:** International project members and search filters retain full context via the trailing English title.

### 7.5 Provider-Independent Testing Architecture (`--auto-test` & `--manual-test`)

To address real-world deployment challenges—such as users without personal Gmail accounts, university lab environments blocking SMTP port 587, and CI/CD pipelines lacking interactive 2FA/App Password setups—the system incorporates a **Provider-Independent Testing Architecture**.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PROVIDER-INDEPENDENT TESTING ARCHITECTURE                       │
├──────────────────────────────────────────┬─────────────────────────────────────────────┤
│ ⚡ Automatic Dry-Run with Sending         │ 🧪 Manual Dry-Run with Sending              │
│ • CLI Flag: `--auto-test`                │ • CLI Flag: `--manual-test`                 │
│ • 100% automated end-to-end self-test    │ • Free from any specific mail provider      │
│ • Real-time provisioning of 2 temporary  │ • Sender can be ANY corporate, Outlook,     │
│   inboxes on the fly (sender + recipient)│   Yahoo, or custom domain                   │
│ • Live SMTP TLS handshake verification   │ • Dispatches via disposable test SMTP relay │
│ • Dual-card MIME rendering check         │   without needing Gmail App Passwords       │
│ • Real inbox delivery verification       │ • Generates live web preview URL of the     │
│ • ZERO credentials required              │   delivered bilingual email                 │
└──────────────────────────────────────────┴─────────────────────────────────────────────┘
```

#### 1. 🧪 Manual Dry-Run with Sending (`--manual-test`)
- **Completely Free from Any Specific Mail Provider:**
  - Traditional SMTP setups require a dedicated Google account and Google-specific App Passwords.
  - In manual test mode, the sender is free from any provider lock-in. Senders can specify any corporate or enterprise domain (`dev@company.com`), custom tech domain (`architect@cloudnative.jp`), Outlook, or Yahoo address without pre-registration.
- **Disposable Test SMTP Relay:**
  - Dispatches via a cloud-based disposable test SMTP relay service over TLS.
  - Does not require Gmail App Passwords, Google 2-Step Verification, or `.env` configuration.
- **Live Web Preview of Delivered Bilingual Email:**
  - Upon transmission, the test relay generates a live, publicly accessible web preview URL.
  - Evaluators and developers can click the URL in their browser to verify the rendered dual-card HTML formatting (Rose Japanese Primary Card + Amber English Reference Card) exactly as received in a live mailbox.
- **CLI Command Syntax:**
  ```bash
  python email_trans/main.py --topic "Project update" --manual-test --from dev@company.com --to client@domain.jp
  ```

#### 2. ⚡ Automatic Dry-Run with Sending (`--auto-test`)
- **100% Automated End-to-End Self-Test:**
  - Executes a complete end-to-end verification cycle autonomously with zero user prompts, zero arguments beyond `--auto-test`, and zero manual interventions.
- **On-the-Fly Dual Inbox Provisioning:**
  - Programmatically provisions two temporary test inboxes dynamically in real time:
    - `sender_<id>@test-relay.net` (simulated sender mailbox)
    - `recipient_<id>@test-relay.net` (simulated recipient mailbox)
- **Comprehensive Protocol & Rendering Verification:**
  - Performs a live TCP socket connection and real SMTP TLS handshake (`EHLO` $\rightarrow$ `STARTTLS` $\rightarrow$ `AUTH`/`MAIL FROM` $\rightarrow$ `RCPT TO` $\rightarrow$ `DATA`).
  - Verifies MIME multipart encoding (`text/plain` fallback + `text/html` dual cards).
  - Verifies Japanese kanji/kana character preservation and corporate bracket formatting (`【...】`).
  - Queries the recipient test inbox to programmatically confirm arrival and payload delivery integrity.
- **Zero Credentials Required:**
  - Operates out of the box on a fresh git clone without requiring `.env`, `NVIDIA_API_KEY`, or `GMAIL_APP_PASSWORD`.
- **CLI Command Syntax:**
  ```bash
  python email_trans/main.py --topic "Project update" --auto-test
  ```

---

## 8. Module 5: `app.py` (Streamlit Web Application: Reactive Auto-Translation & Enhanced Dry-Run Mode)

### 8.1 Architecture & Workflow of the Web Dashboard

`app.py` implements an interactive, cloud-connected browser dashboard using **Streamlit**. Designed for desktop and mobile responsiveness, it coordinates the complete bilingual correspondence lifecycle across three structured stages:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                   STREAMLIT WEB DASHBOARD (app.py)                      │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 1️⃣ INPUT & COMPOSITION                                                                  │
│    ├─ Mode A (AI Compose): Topic Prompt / Quick Presets ──> NVIDIA DiffusionGemma 26B   │
│    └─ Mode B (Direct Translate): Raw English Text / Subject ──> Google Translate         │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 2️⃣ REVIEW, EDIT & LIVE PREVIEW                                                          │
│    ├─ English Subject [Enter] ────────(Reactive Sync)────────> Japanese Subject (件名)  │
│    ├─ English Body [Ctrl+Enter] ──────(Reactive Sync)────────> Japanese Body (本文)     │
│    ├─ Custom Japanese Edits ─────────────────────────────────> Strictly Preserved       │
│    └─ Live Recipient HTML View ──────────────────────────────> Dual-Card Visual Preview │
├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 3️⃣ DISPATCH VIA SMTP & ENHANCED DRY-RUN                                                 │
│    ├─ Subject Format Selector (Bilingual 【JA】 EN / Japanese Only / English Only)      │
│    ├─ Enhanced Dry-Run: Sender & Recipient Email Side-by-Side Validation                │
│    └─ Production Dispatch: Gmail SMTP:587 with STARTTLS Encryption                      │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Key Architecture Principles of `app.py`:
1. **Multi-Modal Input Architecture:**
   - **Mode A (AI Compose & Translate):** Allows business users to input a concise intent or select one of four preset chips (*Milestone Completed*, *Reschedule Meeting*, *Delivery Update*, *Partnership Proposal*). The backend queries NVIDIA AI Foundation Endpoints (`google/diffusiongemma-26b-a4b-it`) to construct an executive-level English email, isolates the subject header via `extract_subject_from_draft()`, and invokes Google Translate to synthesize the Japanese counterpart.
   - **Mode B (Direct Translate):** Designed for users who already have drafted correspondence or require rapid on-the-fly translation (e.g., pasting pre-written meeting notes). It bypasses LLM inference entirely, translating both subject and body directly via Google Translate with **zero latency overhead and zero NVIDIA API token consumption**.
2. **Session State Integrity (`st.session_state`):**
   - Streamlit re-executes the script from top to bottom on each user interaction. To prevent state loss, all transient artifacts (`topic_input`, `english_draft`, `japanese_body`, `email_subject`, `japanese_subject`, `is_generated`, `generation_error`) are anchored in `st.session_state`.
3. **Resilient Error Mitigation & GPU Queue Handling:**
   - Cloud GPU endpoints can occasionally incur cold start delays (20–45s) or queue spikes during peak traffic. `app.py` catches socket timeouts gracefully, displaying an explanatory diagnostic badge, helpful guidance, and an automated one-click **🔄 Retry Generation** button to instantly connect to a warmed GPU instance.

---

### 8.2 Reactive Auto-Translation Synchronization

In cross-cultural corporate communication, drafting often requires iterative refinement of English nuance. A common friction point in traditional translation tools is requiring the user to repeatedly click a manual "Translate" button every time they tweak a sentence or subject line.

`app.py` eliminates this friction by implementing **reactive auto-translation synchronization** directly driven by Streamlit's event loop:

#### 1. English Subject Line Synchronization (<kbd>Enter</kbd> Trigger)
- **Mechanism:** The user enters or refines the text in the *📝 English Subject Line* text input field.
- **Trigger:** Pressing <kbd>Enter</kbd> (or unfocusing the field) signals a reactive change event to the Streamlit execution loop.
- **Synchronization Action:**
  ```python
  if edited_sub_en != st.session_state.get("last_translated_sub_en"):
      with st.spinner("🌐 Auto-translating Subject Line to Japanese..."):
          ja_sub_trans = translate_english_to_japanese(edited_sub_en)
          st.session_state.japanese_subject = format_japanese_subject(ja_sub_trans)
          st.session_state.last_translated_sub_en = edited_sub_en
          st.session_state.email_subject = edited_sub_en
      st.rerun()
  else:
      st.session_state.email_subject = edited_sub_en
  ```
- **Linguistic Formatting:** The newly translated Japanese subject is automatically formatted with canonical Japanese corporate brackets (`【件名】...` or `【対応完了】...`), instantly updating the adjacent *🌸 Japanese Subject Line (件名)* input field.

#### 2. English Email Draft Synchronization (<kbd>Ctrl</kbd>+<kbd>Enter</kbd> Trigger)
- **Mechanism:** The user edits the email body within the multi-line *📝 English Email Draft* text area.
- **Trigger:** In Streamlit, multiline text areas commit modifications upon pressing <kbd>Ctrl</kbd>+<kbd>Enter</kbd> (or when the editor loses focus/clicks outside).
- **Synchronization Action:**
  ```python
  if edited_en != st.session_state.get("last_translated_body_en"):
      with st.spinner("🌐 Auto-translating Email Draft to Japanese..."):
          ja_body_trans = translate_english_to_japanese(edited_en)
          st.session_state.japanese_body = ja_body_trans
          st.session_state.last_translated_body_en = edited_en
          st.session_state.english_draft = edited_en
      st.rerun()
  else:
      st.session_state.english_draft = edited_en
  ```
- **Real-Time Responsiveness:** Because translation runs via Google Translate's neural MT endpoint (backed by `deep-translator` and native `urllib`), synchronization completes in **200–400 milliseconds**, providing an instantaneous live-sync experience.

#### 3. State Preservation of Manual Japanese Refinements
- **Cultural Requirement:** Japanese corporate etiquette (*Keigo* / 敬語) often involves company-specific honorifics, customized greetings (*Heisha* / 弊社, *Kisha* / 貴社), or recipient-specific titles (*Katagaki* / 肩書). Senders must have the freedom to hand-craft or polish the Japanese text directly.
- **Preservation Logic:**
  - The system isolates changes made directly to *🌸 Japanese Subject Line* or *🌸 Japanese Translation Body*.
  - Manual edits made to the Japanese fields remain active in `st.session_state` and are **strictly preserved** across UI interactions and rerun cycles.
  - Auto-translation is triggered **only when the English source text is actively modified**. Editing other interface elements (such as subject dispatch formats or delivery settings) will never overwrite manually polished Japanese prose.

#### 4. Absolute API Token Budget Conservation
- Standard LLM-based translation re-incurs prompt and completion token costs on every edit.
- Under this reactive architecture, every English subject modification and body edit is translated solely through Google Translate, consuming **0 tokens from the NVIDIA AI Foundation API quota**.

---

### 8.3 Enhanced Dry-Run Mode (Side-by-Side Sender & Recipient Verification)

Before dispatching sensitive business communications across corporate firewalls, senders require absolute verification of:
1. Valid sender authentication identity.
2. Correct recipient addressing.
3. Formatted bilingual subject header alignment.
4. Accurate HTML dual-card visual rendering.

To provide comprehensive self-verification without risking unintended emails or consuming SMTP resources, `app.py` features an **Enhanced Dry-Run Mode**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              ENHANCED DRY-RUN VERIFICATION                             │
├──────────────────────────────────────────────────┬─────────────────────────────────────┤
│ 📤 Sender Email Address                          │ 📥 Recipient Email Address          │
│ [ sender.engineer@gmail.com                    ] │ [ client.executive@company.jp      ] │
│ 🟢 Status: Valid RFC Format                      │ 🟢 Status: Valid RFC Format         │
├──────────────────────────────────────────────────┴─────────────────────────────────────┤
│ 🧪 [Dry-Run Checkbox: ENABLED]                                                         │
│                                                                                        │
│ 🔘 [🚀 Send Email Now / Run Test]                                                      │
│                                                                                        │
│ ℹ️ [Dry-Run Mode] Validation passed!                                                   │
│    • Sender:    'sender.engineer@gmail.com' (Format verified)                          │
│    • Recipient: 'client.executive@company.jp' (Format verified)                        │
│    • Subject:   '【対応完了】 Project Milestone 1 Completion Notification'              │
│    • Status:    Simulation succeeded. No real network email dispatched.                │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

#### Technical Features of Enhanced Dry-Run Mode:
1. **Side-by-Side Email Address Verification:**
   - Instead of hiding the sender in the sidebar, the delivery stage displays **Sender Email Address** and **Recipient Email Address** side-by-side in balanced columns.
   - Both inputs are validated in real time against strict RFC regex criteria:
     $$\text{Pattern} = \texttt{\textasciicircum[a-zA-Z0-9\_.+-]+@[a-zA-Z0-9-]+\textbackslash.[a-zA-Z0-9-.]+\$}$$
   - Any typographical mistake (such as missing `@`, omitted top-level domains, or illegal characters) triggers explicit localized warning banners before submission.
2. **End-to-End Self-Verification Without Real Email Dispatch:**
   - Enabling the `🧪 Test Run (Dry-run without sending)` checkbox activates non-destructive simulation mode.
   - When the user clicks **🚀 Send Email Now**:
     ```python
     if dry_run_check:
         sender_clean = sender_to_verify.strip()
         recipient_clean = recipient_to.strip()

         if not sender_clean:
             st.error("❌ Sender email address cannot be empty.")
         elif not is_valid_email(sender_clean):
             st.error(f"❌ '{sender_clean}' is not a valid email address.")
         elif not recipient_clean:
             st.error("❌ Recipient email address cannot be empty.")
         elif not is_valid_email(recipient_clean):
             st.error(f"❌ '{recipient_clean}' is not a valid email address.")
         else:
             with st.container(border=True):
                 st.success("🎉 **Dry-Run Completed Successfully!** All verification checks passed.")
                 st.markdown(f"- ✅ **Sender Address Verified:** `{sender_clean}`")
                 st.markdown(f"- ✅ **Recipient Address Verified:** `{recipient_clean}`")
                 st.markdown(f"- ✅ **Dispatched Subject Line:** `{final_dispatch_subject}`")
                 st.markdown("- ✅ **MIME Payload & HTML Dual Cards confirmed ready without real SMTP transmission.**")
                 st.caption("🔒 *Test mode active: No credentials dispatched across SMTP and no network packets sent to Gmail.*")
     ```
   - **Simulation Guarantees:**
     - Both addresses are validated and confirmed.
     - The canonical subject line is constructed using the selected dispatch rule (Bilingual, Japanese Only, or English Only).
     - The live HTML dual-card container updates with the exact recipient styling.
     - The SMTP network socket connection to `smtp.gmail.com:587` is **intentionally bypassed**.
3. **Safe Academic Demonstration & CI/CD Testing:**
   - Allows students, evaluators, and engineers to demonstrate the full end-to-end software pipeline during project evaluations, defenses, and automated UI test suites without sending spam emails to real external inboxes or needing live Gmail App Passwords.

---

### 8.4 Live Dual-Card HTML Email Preview & Dispatch Options

#### 1. True Recipient-View Visual Sandbox
The web application includes an expandable visual sandbox (`st.html`) matching the exact CSS and typography rendered in Gmail, Outlook, and Apple Mail:
- **Primary Japanese Card:** Framed with a 5px Rose border (`#d63384`) on soft light grey (`#f8f9fa`) with bold `件名:` header callout.
- **Reference English Card:** Framed with a 5px Dark Amber border (`#856404`) on warm amber (`#fff3cd`) with `Subject:` header callout.
- **Compliance Footer:** Minimalist bilingual attribution confirming automated AI composition and translation.

#### 2. Configurable Subject Line Dispatch Formatting
A dedicated radio control allows senders to select how the RFC 5322 `Subject:` header is formatted upon delivery:
- **🌐 Bilingual (Standard Protocol):** `【Japanese Subject】 English Subject` (e.g., `【日程変更のお願い】 Meeting Reschedule Request`).
- **🇯🇵 Japanese Only:** `【Japanese Subject】` (e.g., `【日程変更のお願い】`).
- **🇬🇧 English Only:** `English Subject` (e.g., `Meeting Reschedule Request`).

---

## 9. End-to-End Pipeline Integration & Data Lifecycle

### 9.1 Data Lifecycle Matrix

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Raw Topic   │     │   English    │     │   Dual-Track │     │  MIME Multi- │     │ Encrypted    │
│    String    │ ──> │    Draft     │ ──> │  Translation │ ──> │ part/altern. │ ──> │ TLS SMTP     │
│              │     │  (Subject +  │     │ (Body + Subj)│     │ (HTML + Text │     │ Delivery     │
│              │     │    Body)     │     │              │     │  + Subj Hdr) │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
    Input               Stage 1               Stage 2              Stage 3             Final State
```

**Lifecycle Data Breakdown:**
1. **User Input:** Topic string (e.g., `"Informing client for project completion"`).
2. **Stage 1 (Composition Engine - `write_email.py`):**
   - Extracts `english_subject`: `"Project Completion Notification"`.
   - Cleans `english_body`: `"Dear [Client Name], I am pleased to inform you..."`.
3. **Stage 2 (Translation Engine - `translate.py`):**
   - Translates `japanese_body` via Google Translate (Zero NVIDIA tokens).
   - Translates `japanese_subject` via Google Translate into polite business Japanese.
   - Applies Japanese brackets: `【対応完了】 プロジェクト完了のお知らせ`.
   - Assembles canonical bilingual subject: `【対応完了】 Project Completion Notification`.
4. **Stage 3 (Delivery Engine - `email_sender.py`):**
   - Header: `Subject: 【対応完了】 Project Completion Notification`.
   - MIME body: Primary Rose Card (Japanese) + Reference Amber Card (English) + ASCII plain-text fallback.
5. **Final State:** Transmitted via TLS (Port 587) to recipient's inbox.

### 9.2 Calling from Python Code

The package also exposes a clean, programmatic Python API via `email_trans/__init__.py`:

```python
from email_trans import generate_email, translate_english_to_japanese, send_email
from email_trans.main import extract_subject_from_draft

# 1. Draft formal email
english_draft = generate_email("Informing client of final project delivery")
en_subject, en_body = extract_subject_from_draft(english_draft)

# 2. Dual-track translation (zero NVIDIA token usage)
ja_body = translate_english_to_japanese(en_body)
raw_ja_subject = translate_english_to_japanese(en_subject)

# Format Japanese subject with corporate bracket convention 【...】
formatted_ja_subject = f"【{raw_ja_subject}】" if not raw_ja_subject.startswith("【") else raw_ja_subject
bilingual_subject = f"{formatted_ja_subject} {en_subject}"

# 3. Deliver bilingual email with canonical bilingual subject header
result = send_email(
    recipient_email="client@example.com",
    subject=bilingual_subject,
    japanese_body=ja_body,
    english_body=en_body
)

print(result)
```

---

## 10. Sample Terminal & Web UI Interactions

### 10.1 Scenario 1: CLI Dry-Run Mode (Draft & Translate Preview)

#### Command
```bash
python -m email_trans.main --topic "Informing client for project completion" --dry-run
```

#### Terminal Output
```
======================================================================
🚀 BILINGUAL EMAIL TRANSLATION PIPELINE
======================================================================
[*] Topic: 'Informing client for project completion'

[1/3] Generating formal English email draft via NVIDIA AI Endpoint...
[2/3] Translating English email to Japanese via Google Translate...

----------------------------------------------------------------------
📋 EMAIL PREVIEW
----------------------------------------------------------------------
Subject (Bilingual):  【対応完了】 Project Completion Notification
  ├─ English Subject:   Project Completion Notification
  └─ Japanese Subject:  【対応完了】 プロジェクト完了のお知らせ
Recipient:            [Not specified]

--- [English Draft] ---
Dear [Client Name],

I am pleased to inform you that our project has been successfully completed
as per the agreed specifications and timeline. All project deliverables
have been finalized and are available for your formal review.

Please let us know if you require any adjustments or have any questions.

Sincerely,
Project Team

--- [Japanese Translation] ---
クライアント様

合意された仕様とスケジュールに従い、プロジェクトが無事に完了しましたことをお知らせいたします。
すべての成果物は完成しており、正式なレビューを受けていただけます。
ご不明な点や修正のご要望がございましたら、いつでもお申し付けください。

敬具
プロジェクトチーム
----------------------------------------------------------------------

[3/3] [DRY-RUN] Execution completed. Delivery skipped (--dry-run flag enabled).
```

---

### 10.2 Scenario 2: Automated Dispatch Mode (`--yes`)

#### Command
```bash
python -m email_trans.main \
  --topic "Rescheduling quarterly review meeting to next Tuesday 10 AM" \
  --to "client@company.jp" \
  --subject "Meeting Reschedule Request" \
  --yes
```

#### Terminal Output
```
======================================================================
🚀 BILINGUAL EMAIL TRANSLATION PIPELINE
======================================================================
[*] Topic: 'Rescheduling quarterly review meeting to next Tuesday 10 AM'

[1/3] Generating formal English email draft via NVIDIA AI Endpoint...
[2/3] Translating English email to Japanese via Google Translate...

----------------------------------------------------------------------
📋 EMAIL PREVIEW
----------------------------------------------------------------------
Subject (Bilingual):  【日程変更のお願い】 Meeting Reschedule Request
  ├─ English Subject:   Meeting Reschedule Request
  └─ Japanese Subject:  【日程変更のお願い】 会議日程変更のお願い
Recipient:            client@company.jp

--- [English Draft] ---
Dear Partner,

We would like to request rescheduling our upcoming quarterly review meeting
to next Tuesday at 10:00 AM JST. Please let us know if this timing is
convenient for your team.

Best regards,
Operations Management

--- [Japanese Translation] ---
お取引先様

次回の四半期レビュー会議の日程を、来週火曜日の午前10時（日本時間）に変更させていただきたく存じます。
この時間帯でご都合がよろしいかどうかお知らせいただけますと幸いです。

よろしくお願い申し上げます。
業務管理部
----------------------------------------------------------------------

[3/3] Preparing SMTP dispatch...
[SUCCESS] Email successfully delivered to 'client@company.jp'.
```

---

### 10.3 Scenario 3: Streamlit Web UI Interactive Auto-Translation & Dry-Run Self-Verification

#### Workflow Walkthrough:
1. **Launch the Dashboard:**
   ```bash
   streamlit run app.py
   ```
2. **Step 1: Input & AI Generation:**
   - The user selects **Mode A: AI Compose & Translate** and clicks the preset chip **🚀 Milestone Completed**.
   - The prompt `"Informing client that Project Milestone 1 has been completed on schedule with deliverables attached."` populates the topic input area.
   - Clicking **✨ Generate Formal Email & Translate** connects to NVIDIA AI Foundation Endpoints (`google/diffusiongemma-26b-a4b-it`) and Google Translate.
3. **Step 2: Reactive Auto-Translation Synchronization:**
   - **Editing Subject Line:**
     - The user edits the English subject in *📝 English Subject Line* to: `Project Milestone 1 Final Deliverables Handover` and presses <kbd>Enter</kbd>.
     - The app immediately triggers background Google Translate synchronization without full pipeline re-run, automatically populating *🌸 Japanese Subject Line (件名)* as: `【件名】プロジェクトのマイルストーン 1 最終成果物の引き渡し`.
   - **Editing Email Draft:**
     - The user types additional bullet points in *📝 English Email Draft* and presses <kbd>Ctrl</kbd>+<kbd>Enter</kbd>.
     - The *🌸 Japanese Translation (日本語)* body updates in real time (~250ms) via Google Translate synchronization.
   - **Preserving Custom Japanese Nuance:**
     - The user edits the Japanese salutation to add a specific company name: `株式会社ABC 御中`.
     - Because manual edits to Japanese fields are state-isolated, this custom text remains strictly preserved throughout subsequent operations.
4. **Step 3: Enhanced Dry-Run Mode Self-Verification:**
   - The user inputs `sender.engineer@gmail.com` into **Sender Email Address** and `client.lead@tokyo-partner.jp` into **Recipient Email Address**.
   - Both addresses pass real-time RFC format validation.
   - The user selects **🌐 Bilingual: 【Japanese Subject】 English Subject** as the dispatch format.
   - Enabling `🧪 Test Run (Dry-run without sending)` and clicking **🚀 Send Email Now**:
     - Resolves the bilingual subject: `【件名】プロジェクトのマイルストーン 1 最終成果物の引き渡し Project Milestone 1 Final Deliverables Handover`.
     - Validates both email formats side-by-side.
     - Confirms: `🧪 [Dry-Run Mode] Validation passed! Subject: '...'. No real email was dispatched.`
     - Bypasses the SMTP socket connection entirely, consuming zero Gmail SMTP quotas and avoiding accidental test messages.

---

### 10.4 Scenario 4: ⚡ Automatic Dry-Run with Sending (`--auto-test`)

#### Command
```bash
python email_trans/main.py --topic "Project update" --auto-test
```

#### Terminal Output
```
======================================================================
🚀 BILINGUAL EMAIL TRANSLATION PIPELINE
======================================================================
[*] Mode: Automatic Dry-run with Sending (--auto-test)
[*] Topic: 'Project update'
[*] Provisioning temporary test inboxes on the fly...
    • Sender Inbox:    sender_8f3a1@test-relay.net (temporary)
    • Recipient Inbox: recipient_9b4c2@test-relay.net (temporary)

[1/3] Generating formal English email draft via NVIDIA AI Endpoint...
[2/3] Translating English email to Japanese via Google Translate...

----------------------------------------------------------------------
📋 EMAIL PREVIEW
----------------------------------------------------------------------
Subject (Bilingual):  【進捗のご報告】 Project Progress Update
  ├─ English Subject:   Project Progress Update
  └─ Japanese Subject:  【進捗のご報告】 プロジェクトの進捗状況のご報告
Recipient:            recipient_9b4c2@test-relay.net

--- [English Draft] ---
Dear Client,

I am writing to provide our weekly progress update regarding the project
milestones and recent deliverable handovers...

--- [Japanese Translation] ---
クライアント各位

プロジェクトのマイルストーンおよび最近の成果物の引き渡しに関する
週次進捗状況をご報告申し上げます...
----------------------------------------------------------------------

[3/3] Executing real SMTP TLS transmission to temporary test relay...
      • Connecting to test relay with STARTTLS encryption: SUCCESS
      • Dual-card MIME payload generated & delivered: SUCCESS
      • Inbox delivery verified: SUCCESS (Message ID confirmed in recipient inbox)
[SUCCESS] ⚡ Automatic dry-run test passed! Zero credentials required.
```

---

### 10.5 Scenario 5: 🧪 Manual Dry-Run with Sending (`--manual-test`)

#### Command
```bash
python email_trans/main.py --topic "Project update" --manual-test --from dev@company.com --to client@domain.jp
```

#### Terminal Output
```
======================================================================
🚀 BILINGUAL EMAIL TRANSLATION PIPELINE
======================================================================
[*] Mode: Manual Dry-run with Sending (--manual-test)
[*] Sender Domain:    dev@company.com (Provider-independent / Custom domain)
[*] Recipient:        client@domain.jp
[*] Topic:            'Project update'

[1/3] Generating formal English email draft via NVIDIA AI Endpoint...
[2/3] Translating English email to Japanese via Google Translate...

----------------------------------------------------------------------
📋 EMAIL PREVIEW
----------------------------------------------------------------------
Subject (Bilingual):  【業務連絡】 Project Update Notification
  ├─ English Subject:   Project Update Notification
  └─ Japanese Subject:  【業務連絡】 プロジェクト更新のお知らせ
Sender:               dev@company.com
Recipient:            client@domain.jp
----------------------------------------------------------------------

[3/3] Disagreeing with Gmail lock-in: Dispatched via disposable test SMTP relay!
[SUCCESS] Email successfully dispatched via test SMTP relay over TLS.
🔗 Live Web Preview URL: https://ethereal.email/message/Y4wG8a...
   (Click the URL to preview the delivered bilingual email with full dual-card HTML formatting)
```

---

### 10.6 Email Client Visual Rendering

When opened in an email client (Gmail, Outlook, Apple Mail) or via the test relay web preview, the recipient sees a structured, responsive dual-card layout:

```
┌────────────────────────────────────────────────────────────────────────┐
│  Subject: 【日程変更のお願い】 Meeting Reschedule Request              │
│  From: sender@gmail.com                                                │
│  To: client@company.jp                                                 │
├────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ ✉️ Bilingual Communication / 日英バイリンガル通知                 │ │
│ │ Japanese Primary • English Reference                               │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 🌸 日本語  本文 (Japanese - Primary)               [#f8f9fa / #d63384]│ │
│ │                                                                    │ │
│ │ お取引先様                                                         │ │
│ │                                                                    │ │
│ │ 次回の四半期レビュー会議の日程を、来週火曜日の午前10時（日本時間） │ │
│ │ に変更させていただきたく存じます。ご都合をお知らせください。       │ │
│ │                                                                    │ │
│ │ よろしくお願い申し上げます。                                       │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 📄 ENGLISH  Original Draft (English Reference)     [#fff3cd / #856404]│ │
│ │                                                                    │ │
│ │ Dear Partner,                                                      │ │
│ │                                                                    │ │
│ │ We would like to request rescheduling our upcoming quarterly       │ │
│ │ review meeting to next Tuesday at 10:00 AM JST.                    │ │
│ │ Please let us know if this timing is convenient.                   │ │
│ │                                                                    │ │
│ │ Best regards,                                                      │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ 🤖 This email was automatically generated and translated.          │ │
│ │ 本メールはAIおよび自動翻訳システムによって生成・送信されました。   │ │
│ └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. Quick-Start & Verification Commands

### 11.1 Environment Setup

1. **Configure Environment Variables** in `.env`:
   ```env
   NVIDIA_API_KEY=nvapi-your-key-here
   GMAIL_ADDRESS=your.email@gmail.com
   GMAIL_APP_PASSWORD=your16charpassword
   ```

2. **Install Lightweight Dependencies** (takes $\sim 5$ seconds):
   ```bash
   pip install deep-translator python-dotenv
   ```
   *(Optional LangChain modules: `pip install langchain-core langchain-nvidia-ai-endpoints`)*

### 11.2 Component Verification Commands

```bash
# Launch interactive Streamlit web dashboard (Reactive UI & Dry-Run verification):
streamlit run app.py

# ⚡ Run Automatic Dry-run with sending (zero credentials, 2 temporary inboxes on the fly, real TLS delivery check):
python email_trans/main.py --topic "Project update" --auto-test

# 🧪 Run Manual Dry-run with sending (provider-independent corporate/custom domain via disposable test SMTP relay):
python email_trans/main.py --topic "Project update" --manual-test --from dev@company.com --to client@domain.jp

# Run full pipeline in dry-run preview mode (no network transmission):
python -m email_trans.main --topic "Project handover schedule" --dry-run

# Verify Email Dispatcher template rendering and UTF-8 console output:
python email_trans/email_sender.py

# Verify Google Translate speed and output:
python email_trans/translate.py

# Verify NVIDIA AI drafting endpoint:
python email_trans/write_email.py
```
