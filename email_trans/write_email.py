"""
Email composition module powered by NVIDIA AI Foundation Endpoints.
Uses cloud-hosted LLMs (e.g. google/diffusiongemma-26b-a4b-it or meta/llama-3.1-70b-instruct).
Zero local VRAM/disk usage. Compatible with Python 3.14.2.
"""

import os
import sys
import json
import urllib.request
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

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return res_data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"NVIDIA API HTTP {exc.code}: {err_body}") from exc
    except Exception as exc:
        raise RuntimeError(f"NVIDIA API Connection Error: {exc}") from exc


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
