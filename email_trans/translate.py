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


import sys

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


def translate_with_google_http(text: str, source: str = "en", target: str = "ja") -> str:
    """
    Direct HTTP fallback to Google Translate endpoints without external dependencies.
    Tries Chrome extension client first, then GTX, then MyMemory fallback.
    100% compatible with Python 3.14.2 standard library.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Endpoint 1: clients5.google.com (Chrome Extension endpoint, highly reliable)
    try:
        url_chrome = (
            "https://clients5.google.com/translate_a/t?"
            + urllib.parse.urlencode({
                "client": "dict-chrome-ex",
                "sl": source,
                "tl": target,
                "q": text,
            })
        )
        req = urllib.request.Request(url_chrome, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and data:
                return "".join(data)
            elif isinstance(data, str):
                return data
    except Exception:
        pass

    # Endpoint 2: translate.googleapis.com single gtx
    try:
        url_gtx = (
            "https://translate.googleapis.com/translate_a/single?"
            + urllib.parse.urlencode({
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text,
            })
        )
        req = urllib.request.Request(url_gtx, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            translated_segments = [segment[0] for segment in data[0] if segment and segment[0]]
            if translated_segments:
                return "".join(translated_segments)
    except Exception:
        pass

    # Endpoint 3: MyMemory API translation fallback
    try:
        url_mymemory = (
            "https://api.mymemory.translated.net/get?"
            + urllib.parse.urlencode({
                "q": text[:500],
                "langpair": f"{source}|{target}",
            })
        )
        req = urllib.request.Request(url_mymemory, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            res_text = data.get("responseData", {}).get("translatedText")
            if res_text:
                return res_text
    except Exception:
        pass

    raise RuntimeError("All Google Translate and fallback translation endpoints failed.")


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
