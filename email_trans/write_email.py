"""
Email composition module powered by NVIDIA AI Foundation Endpoints.
Uses cloud-hosted LLMs (e.g. google/diffusiongemma-26b-a4b-it or meta/llama-3.2-11b-vision-instruct).
Zero local VRAM/disk usage. Compatible with Python 3.14.2.
"""

import os
import sys
import json
import time
import socket
import http.client
import urllib.request
import urllib.error
from typing import Optional
from dotenv import load_dotenv

# Ensure Unicode prints properly on Windows terminal
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

NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
DEFAULT_MODEL = os.getenv("NVIDIA_MODEL", "google/diffusiongemma-26b-a4b-it")
SECONDARY_MODEL = os.getenv("NVIDIA_SECONDARY_MODEL", "meta/llama-3.2-11b-vision-instruct")

DEFAULT_TIMEOUT = 60  # Increased from 30s to 60s for reliable generation
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_DELAYS = (2.0, 4.0)
DEFAULT_MAX_TOKENS = 512
REDUCED_MAX_TOKENS = 384


def _is_timeout_error(exc: Exception) -> bool:
    """Checks whether an exception was caused by a socket or HTTP timeout."""
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in (408, 504)
    if isinstance(exc, urllib.error.URLError):
        if isinstance(exc.reason, (TimeoutError, socket.timeout)):
            return True
        reason_str = str(exc.reason).lower()
        if "timed out" in reason_str:
            return True
    return "timed out" in str(exc).lower()


def _is_transient_error(exc: Exception) -> bool:
    """Checks whether an exception is transient and eligible for retry."""
    if _is_timeout_error(exc):
        return True
    if isinstance(exc, urllib.error.HTTPError):
        # 429 Too Many Requests, 500 Internal, 502 Bad Gateway, 503 Unavailable, 504 Gateway Timeout
        return exc.code in (429, 500, 502, 503, 504)
    if isinstance(exc, urllib.error.URLError):
        reason_str = str(exc.reason).lower()
        return any(term in reason_str for term in ("connection reset", "remote end closed", "temporary failure", "refused", "eof occurred"))
    if isinstance(exc, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, http.client.RemoteDisconnected)):
        return True
    return False


def _send_completion_request(
    endpoint: str,
    api_key: str,
    model: str,
    topic: str,
    temperature: float = 0.5,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    timeout: int = DEFAULT_TIMEOUT,
) -> str:
    """Executes a single HTTP request to the NVIDIA OpenAI-compatible chat completions endpoint."""
    payload = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional corporate email writer. "
                    "Write in a formal, polite, and concise tone. "
                    "Include a clear subject line and formatted body."
                )
            },
            {
                "role": "user",
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

    with urllib.request.urlopen(req, timeout=timeout) as response:
        res_data = json.loads(response.read().decode("utf-8"))
        choices = res_data.get("choices", [])
        if not choices:
            raise RuntimeError("NVIDIA API returned empty response choices.")
        content = choices[0].get("message", {}).get("content", "")
        if not content:
            raise RuntimeError("NVIDIA API returned empty message content.")
        return content


def generate_email_with_langchain(topic: str, model_name: Optional[str] = None, temperature: float = 0.5) -> str:
    """Generates formal email using LangChain and ChatNVIDIA."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_nvidia_ai_endpoints import ChatNVIDIA

    effective_model = model_name or os.getenv("NVIDIA_MODEL", DEFAULT_MODEL)

    try:
        llm = ChatNVIDIA(
            base_url=f"{NVIDIA_BASE_URL.rstrip('/')}/",
            model=effective_model,
            temperature=temperature,
            timeout=DEFAULT_TIMEOUT,
        )
    except TypeError:
        llm = ChatNVIDIA(
            base_url=f"{NVIDIA_BASE_URL.rstrip('/')}/",
            model=effective_model,
            temperature=temperature,
        )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional corporate email writer. Write in a formal, polite, and concise tone. Include a clear subject line and formatted body."),
        ("human", "Write a professional email about: {topic}"),
    ])

    chain = prompt | llm
    result = chain.invoke({"topic": topic})
    return str(result.content)


def generate_email_with_http(
    topic: str,
    model_name: Optional[str] = None,
    temperature: float = 0.5,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """
    Direct HTTP request to NVIDIA OpenAI-compatible completions API with:
    1. Socket timeout increased to 60 seconds.
    2. Automatic retry logic (up to 3 attempts with exponential backoff: 2s, 4s).
    3. Fallback to fast secondary model or reduced max_tokens (384 tokens) if primary times out.
    """
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable is not set. Please configure it in .env.")

    endpoint = f"{NVIDIA_BASE_URL.rstrip('/')}/chat/completions"
    primary_model = model_name or os.getenv("NVIDIA_MODEL", DEFAULT_MODEL)
    backoff_delays = DEFAULT_BACKOFF_DELAYS

    last_error: Optional[Exception] = None
    had_timeout = False

    # Attempt primary model with up to 3 attempts and exponential backoff: 2s, 4s
    for attempt in range(max_retries):
        try:
            return _send_completion_request(
                endpoint=endpoint,
                api_key=api_key,
                model=primary_model,
                topic=topic,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        except Exception as exc:
            last_error = exc
            if _is_timeout_error(exc):
                had_timeout = True

            if attempt < max_retries - 1 and _is_transient_error(exc):
                delay = backoff_delays[attempt] if attempt < len(backoff_delays) else backoff_delays[-1]
                print(f"[write_email] Attempt {attempt + 1}/{max_retries} for '{primary_model}' encountered transient issue ({exc}). Retrying in {delay}s...")
                time.sleep(delay)
            else:
                break

    # If all attempts for primary model fail due to timeout (or model deprecation 404/410), attempt fallbacks
    is_deprecated_or_not_found = (
        isinstance(last_error, urllib.error.HTTPError) and last_error.code in (404, 410)
    )

    if had_timeout or is_deprecated_or_not_found:
        secondary_model = os.getenv("NVIDIA_SECONDARY_MODEL", SECONDARY_MODEL)

        # Fallback A: Attempt fast secondary model with reduced max_tokens (384)
        if secondary_model and secondary_model != primary_model:
            reason = "timed out" if had_timeout else f"returned HTTP {getattr(last_error, 'code', 'error')}"
            print(f"[write_email] Primary model '{primary_model}' {reason}. Falling back to fast secondary model '{secondary_model}' (max_tokens={REDUCED_MAX_TOKENS}, timeout={timeout}s)...")
            try:
                return _send_completion_request(
                    endpoint=endpoint,
                    api_key=api_key,
                    model=secondary_model,
                    topic=topic,
                    temperature=temperature,
                    max_tokens=REDUCED_MAX_TOKENS,
                    timeout=timeout,
                )
            except Exception as sec_exc:
                print(f"[write_email] Secondary model '{secondary_model}' failed ({sec_exc}).")
                last_error = sec_exc

        # Fallback B: Retry primary model with reduced max_tokens (384) if secondary model wasn't used or failed
        if not is_deprecated_or_not_found:
            print(f"[write_email] Retrying primary model '{primary_model}' with reduced max_tokens={REDUCED_MAX_TOKENS} (timeout={timeout}s)...")
            try:
                return _send_completion_request(
                    endpoint=endpoint,
                    api_key=api_key,
                    model=primary_model,
                    topic=topic,
                    temperature=temperature,
                    max_tokens=REDUCED_MAX_TOKENS,
                    timeout=timeout,
                )
            except Exception as red_exc:
                print(f"[write_email] Reduced token retry failed ({red_exc}).")
                last_error = red_exc

    # If all attempts and fallbacks failed, raise descriptive error matching application format
    if isinstance(last_error, urllib.error.HTTPError):
        err_body = last_error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"NVIDIA API HTTP {last_error.code}: {err_body}") from last_error
    elif last_error:
        raise RuntimeError(f"NVIDIA API Connection Error: {last_error}") from last_error
    else:
        raise RuntimeError("NVIDIA API failed to generate email.")


def generate_email(topic: str, model_name: Optional[str] = None) -> str:
    """
    Main entrypoint for email generation via NVIDIA AI Endpoint.
    Attempts LangChain first; gracefully falls back to lightweight native HTTP.
    """
    selected_model = model_name or os.getenv("NVIDIA_MODEL", DEFAULT_MODEL)
    try:
        return generate_email_with_langchain(topic, model_name=selected_model)
    except Exception:
        return generate_email_with_http(topic, model_name=selected_model)


if __name__ == "__main__":
    test_topic = sys.argv[1] if len(sys.argv) > 1 else "resolve ticket"
    print(f"Generating formal email for topic: '{test_topic}'...")
    try:
        content = generate_email(test_topic)
        print("\n--- Generated Email ---\n")
        print(content)
    except Exception as exc:
        print(f"Error: {exc}")
