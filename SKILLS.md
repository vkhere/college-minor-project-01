# Skills Matrix & Technical Competency

## Project: English-to-Japanese Email Translator (Cloud AI + Google Translate Edition)
**Academic Context:** College Minor Project  
**Tech Stack:** Python 3.10 – 3.14.2, NVIDIA AI Endpoints (LangChain/HTTP), Google Translate (`deep-translator`), SMTP / MIME  

---

## 1. Technical Skills Matrix

| Skill Category | Specific Competency | Proficiency Level | Implementation in Codebase |
|---|---|---|---|
| **Python Development** | Standard Library & Modern Syntax | ⭐⭐⭐⭐⭐ Expert | Clean modular architecture, `urllib`, `smtplib`, `email.mime`, `argparse`, `json`, full compatibility with Python 3.14.2. |
| **Generative AI** | Cloud LLM Integration & Prompting | ⭐⭐⭐⭐⭐ Expert | Integration with NVIDIA AI Endpoints (`google/diffusiongemma-26b-a4b-it` / Llama models), structured prompt templates, token optimization. |
| **API Optimization** | Token & Quota Conservation | ⭐⭐⭐⭐⭐ Expert | Strategic architectural separation: using LLMs solely for creative drafting while offloading deterministic translation to Google Translate to protect API limits. |
| **Machine Translation** | Cross-Lingual Pipeline Integration | ⭐⭐⭐⭐ Advanced | Integration with Google Translate via `deep-translator` with zero-dependency HTTP fallback for English-to-Japanese conversion. |
| **Email Architecture** | MIME Protocols & HTML Templating | ⭐⭐⭐⭐⭐ Expert | Dual-language `multipart/alternative` email construction with responsive card layouts and STARTTLS encryption. |
| **Environment & DevOps** | Dependency & Security Management | ⭐⭐⭐⭐⭐ Expert | Secrets isolation via `.env`, minimal dependency footprint (<20MB vs >4GB previously), elimination of C-compiler toolchain dependencies. |

---

## 2. Key Architecture Comparison (Before vs After)

| Dimension | Original Minor Project Architecture | Refactored Cloud + Google Translate Architecture |
|---|---|---|
| **Python Version Support** | Limited to Python 3.10 / 3.11 | **Full compatibility with Python 3.10 – 3.14.2** |
| **Dependencies** | `torch`, `transformers`, `sentencepiece`, `sacremoses` | `deep-translator`, `python-dotenv`, `requests` (Zero C-extensions) |
| **Disk Footprint** | ~4.5 GB (PyTorch wheels + 2.4GB NLLB weights) | **< 20 MB** (Zero local model weights) |
| **RAM / VRAM Usage** | > 4 GB RAM / CUDA VRAM | **< 100 MB RAM** |
| **Translation Engine** | Local Seq2Seq model running on PyTorch | **Google Translate API / `deep-translator`** |
| **NVIDIA API Token Load** | Dependent on LLM availability | **Protected: Tokens used only for mail drafting** |
| **Setup Time** | 20–45 minutes (downloading models & wheels) | **< 30 seconds (`pip install -r requirements.txt`)** |

---

## 3. Academic & Domain Learnings

1. **Strategic API Delegation:** Instead of forcing one multi-billion parameter model to perform every task, real-world software engineering excels by selecting the right tool for each job: LLMs for open-ended creative generation, specialized translation engines for linguistics.
2. **Platform & Runtime Portability:** Heavy compiled dependencies like PyTorch are susceptible to wheel-availability delays on new Python minor releases (such as Python 3.14). Decoupling via REST APIs and lightweight HTTP wrappers guarantees high portability across any OS and runtime version.
3. **Enterprise Email Delivery:** Designing resilient multipart emails that maintain visual hierarchy (Japanese highlighted for domestic recipients with English preserved for reference) adheres to international business standards.
