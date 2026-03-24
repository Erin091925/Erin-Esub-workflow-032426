from __future__ import annotations

import os
import io
import re
import json
import time
import uuid
import random
import textwrap
import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# Optional dependencies (graceful fallback)
try:
    import yaml  # pyyaml
except Exception:
    yaml = None

try:
    import pandas as pd
except Exception:
    pd = None

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    import requests
except Exception:
    requests = None


# -----------------------------
# Constants & Catalogs
# -----------------------------

TZ_NAME = "Asia/Taipei"

PANTONE_PALETTES = {
    "Classic Blue (19-4052)": {"accent": "#0F4C81", "accent2": "#08304f"},
    "Peach Fuzz (13-1023)": {"accent": "#FFBE98", "accent2": "#f08a5d"},
    "Very Peri (17-3938)": {"accent": "#6667AB", "accent2": "#4b4c8f"},
    "Illuminating & Ultimate Gray": {"accent": "#F5DF4D", "accent2": "#939597"},
    "Living Coral (16-1546)": {"accent": "#FF6F61", "accent2": "#d65a50"},
    "Ultra Violet (18-3838)": {"accent": "#5F4B8B", "accent2": "#3f2f64"},
    "Greenery (15-0343)": {"accent": "#88B04B", "accent2": "#5f7f32"},
    "Marsala (18-1438)": {"accent": "#955251", "accent2": "#6b3a39"},
    "Emerald (17-5641)": {"accent": "#009B77", "accent2": "#006a51"},
    "Tangerine Tango (17-1463)": {"accent": "#DD4124", "accent2": "#a42d18"},
}

PAINTER_STYLES = [
    "Monet Mist",
    "Van Gogh Vortex",
    "Hokusai Wave",
    "Klimt Gilded Grid",
    "Picasso Cubist Panels",
    "Rothko Color Fields",
    "Pollock Splatter Trace",
    "Vermeer Pearl Light",
    "Rembrandt Shadow Depth",
    "Turner Atmosphere",
    "Matisse Cutout Pop",
    "Cézanne Structure",
    "Dalí Surreal Edge",
    "Kandinsky Geometry",
    "Frida Botanical Bold",
    "Edward Hopper Quiet Neon",
    "Georgia O’Keeffe Bloom",
    "Basquiat Neo-Notes",
    "Magritte Clean Dream",
    "Ink Wash Sumi-e",
]

LANGS = ["English", "繁體中文 (zh-TW)"]
THEMES = ["Light", "Dark"]

# Requested model list (minimum)
MODEL_CATALOG: Dict[str, List[str]] = {
    "OpenAI": ["gpt-4o-mini", "gpt-4.1-mini"],
    "Gemini": [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
    ],
    "Anthropic": [
        # allow user to type / override if their account has other models
        "claude-3-5-sonnet-latest",
        "claude-3-5-haiku-latest",
        "claude-3-opus-latest",
    ],
    "Grok": ["grok-4-fast-reasoning", "grok-3-mini"],
}

FEATURE_KEYS = [
    # Pipeline
    "Pipeline Step 1: FDA Intelligence Summary",
    "Pipeline Step 2: Guidance Review Instructions",
    "Pipeline Step 3: Submission Reorganization",
    "Pipeline Step 4: Final Comprehensive Review",
    # OCR
    "OCR: LLM Multimodal Extraction",
    "OCR: Python PDF Text Extraction",
    # Legacy WOW AI
    "WOW AI: Evidence Mapper",
    "WOW AI: Consistency Guardian",
    "WOW AI: Regulatory Risk Radar",
    "WOW AI: RTA Gatekeeper",
    "WOW AI: Labeling & Claims Inspector",
    # New WOW AI
    "WOW AI: Citation Sentinel",
    "WOW AI: Deficiency Draftsmith",
    "WOW AI: Predicate Differentiator",
    # Agent Runner (default)
    "Agents Runner: Default",
]

DEFAULT_MAX_TOKENS = 12000


# -----------------------------
# i18n (minimal, extendable)
# -----------------------------
I18N = {
    "English": {
        "app_title": "FDA 510(k) Review Studio v3.1 — Nordic WOW",
        "sidebar_title": "Command Center",
        "danger_zone": "Danger Zone",
        "total_purge": "Total Purge (Wipe Session)",
        "managed_by_system": "Managed by System (HF Secrets / Environment)",
        "api_keys": "API Keys",
        "settings_matrix": "Settings Matrix",
        "dashboard": "WOW Command Dashboard",
        "logs": "WOW Event Log Theater",
    },
    "繁體中文 (zh-TW)": {
        "app_title": "FDA 510(k) 審查工作室 v3.1 — Nordic WOW",
        "sidebar_title": "指揮中心",
        "danger_zone": "危險區域",
        "total_purge": "完全清除（清空本次工作階段）",
        "managed_by_system": "由系統管理（HF Secrets / 環境變數）",
        "api_keys": "API 金鑰",
        "settings_matrix": "設定矩陣",
        "dashboard": "WOW 指揮儀表板",
        "logs": "WOW 事件紀錄劇場",
    },
}


# -----------------------------
# Utilities
# -----------------------------

def now_taipei_iso() -> str:
    # Keep simple & deterministic (no pytz dependency). Asia/Taipei is UTC+8.
    dt = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    return dt.replace(microsecond=0).isoformat() + "+08:00"


def safe_preview(text: str, n: int = 180) -> str:
    if not text:
        return ""
    t = re.sub(r"\s+", " ", text).strip()
    return (t[:n] + "…") if len(t) > n else t


def estimate_tokens(text: str) -> int:
    # Provider-agnostic heuristic: ~4 chars/token for English-ish text.
    if not text:
        return 0
    return max(1, int(len(text) / 4))


def word_count(text: str) -> int:
    if not text:
        return 0
    words = re.findall(r"\b\w+\b", text)
    return len(words)


def redact_secrets(s: str) -> str:
    if not s:
        return s
    # Best-effort redaction patterns (avoid over-redacting user docs too aggressively)
    patterns = [
        (r"sk-[A-Za-z0-9]{10,}", "sk-***REDACTED***"),
        (r"AIzaSy[A-Za-z0-9_\-]{10,}", "AIzaSy***REDACTED***"),
        (r"anthropic_[A-Za-z0-9_\-]{10,}", "anthropic_***REDACTED***"),
        (r"xai-[A-Za-z0-9_\-]{10,}", "xai-***REDACTED***"),
    ]
    out = s
    for pat, rep in patterns:
        out = re.sub(pat, rep, out)
    return out


def uuid4_short() -> str:
    return str(uuid.uuid4())[:8]


# -----------------------------
# Session State Initialization
# -----------------------------

def init_state() -> None:
    ss = st.session_state

    ss.setdefault("theme", "Light")
    ss.setdefault("lang", "English")
    ss.setdefault("pantone", list(PANTONE_PALETTES.keys())[0])
    ss.setdefault("painter_style", PAINTER_STYLES[0])
    ss.setdefault("reduce_motion", False)

    # API keys (session-only when not in env)
    ss.setdefault("api_keys_session", {
        "OpenAI": "",
        "Gemini": "",
        "Anthropic": "",
        "Grok": "",
    })

    # Settings matrix
    ss.setdefault("settings_matrix", default_settings_matrix())

    # Artifacts and versions
    # artifacts[name] = [{"id":..., "version":..., "content":..., "meta":...}, ...]
    ss.setdefault("artifacts", {})

    # Pipeline state
    ss.setdefault("pipeline", {
        "step1_input": "",
        "step1_output": "",
        "step2_input": "",
        "step2_output": "",
        "step3_input": "",
        "step3_output": "",
        "step4_input": "",
        "step4_output": "",
        "status": {"step1": "Pending", "step2": "Pending", "step3": "Pending", "step4": "Pending"},
    })

    # Agents runner
    ss.setdefault("agents_yaml_text", default_agents_yaml_text())
    ss.setdefault("agents_parsed", None)
    ss.setdefault("agent_runs", [])  # list of runs with provenance
    ss.setdefault("agent_chain_input", "")  # current working input passed agent-to-agent

    # Upload & OCR buffers
    ss.setdefault("uploads", [])  # list of dicts: {name, bytes, size}
    ss.setdefault("ocr_text_by_file", {})  # filename -> extracted markdown/text

    # Logging & observability
    ss.setdefault("privacy_mode", True)
    ss.setdefault("events", [])  # list of event dicts
    ss.setdefault("provider_stats", {
        "OpenAI": {"calls": 0, "failures": 0, "last_latency_ms": None, "tokens_in": 0, "tokens_out": 0},
        "Gemini": {"calls": 0, "failures": 0, "last_latency_ms": None, "tokens_in": 0, "tokens_out": 0},
        "Anthropic": {"calls": 0, "failures": 0, "last_latency_ms": None, "tokens_in": 0, "tokens_out": 0},
        "Grok": {"calls": 0, "failures": 0, "last_latency_ms": None, "tokens_in": 0, "tokens_out": 0},
    })


def default_settings_matrix() -> Dict[str, Dict[str, Any]]:
    base = {}
    for k in FEATURE_KEYS:
        base[k] = {
            "provider": "OpenAI",
            "model": MODEL_CATALOG["OpenAI"][0],
            "system_prompt": "You are an expert FDA 510(k) reviewer. Be precise, structured, and audit-ready.",
            "user_prompt_template": "{input}",
            "temperature": 0.2,
            "max_tokens": DEFAULT_MAX_TOKENS,
            "output_format": "Markdown",  # Markdown | Text | JSON
            "strict_tone": True,
        }

    # Improve defaults per feature
    base["Pipeline Step 1: FDA Intelligence Summary"]["system_prompt"] = textwrap.dedent("""\
        You are a senior FDA 510(k) reviewer. Produce a comprehensive, audit-ready device context and FDA intelligence summary.
        Requirements:
        - Output must be 2000–3000 words (strict).
        - Use Markdown headings.
        - Include sections: Device Description, Intended Use, Technological Characteristics, Predicate Device Comparison,
          FDA Database Findings (Recalls/Adverse Events), Key Review Risks, and Open Questions.
        - Do not invent citations. If dataset IDs/anchors are unavailable, explicitly say "No source anchor provided."
    """).strip()

    base["Pipeline Step 2: Guidance Review Instructions"]["system_prompt"] = textwrap.dedent("""\
        You are a senior FDA reviewer. Convert guidance text into a device-tailored review instruction manual.
        Requirements:
        - Output must be 2000–3000 words (strict).
        - Must include a Markdown checklist using [ ] syntax.
        - Must include EXACTLY three Markdown tables:
          Table 1: Performance Testing (Test Type | Standard/Method | Acceptance Criteria | Reviewer Notes)
          Table 2: Biocompatibility Endpoints (Tissue Contact Category | Required Endpoints | Justification for Omission)
          Table 3: Labeling & IFU Requirements (Requirement Description | Guidance Reference | Location in Submission)
        - If information is missing, keep the table but mark "Not specified in provided guidance."
    """).strip()

    base["Pipeline Step 3: Submission Reorganization"]["system_prompt"] = textwrap.dedent("""\
        You reorganize sponsor submission summaries to align with reviewer instructions and checklists.
        Requirements:
        - Output in Markdown.
        - Map content into the Step 2 structure.
        - Clearly highlight gaps as "GAP:" items.
        - Avoid fabricating data; if missing, mark as "Not provided in sponsor summary."
    """).strip()

    base["Pipeline Step 4: Final Comprehensive Review"]["system_prompt"] = textwrap.dedent("""\
        You draft an FDA-style 510(k) review report.
        Requirements:
        - Output must be 3000–4000 words (strict).
        - Objective, authoritative tone. Avoid speculation.
        - Include: Executive Summary, Device Description, Intended Use, Predicate Comparison, Performance Testing Review,
          Biocompatibility Review, Sterilization (if relevant), Software/Cybersecurity (if relevant), Labeling Review,
          Deficiencies/Requests for Additional Information, and Recommendation (without making final regulatory decisions).
        - Do not invent citations. If uncertain, add "Reviewer to confirm" notes.
    """).strip()

    base["WOW AI: Citation Sentinel"]["system_prompt"] = textwrap.dedent("""\
        You are a citation and traceability auditor for FDA 510(k) review documents.
        Identify claims that require evidence and whether an anchor/citation is present.
        Output:
        - Citation Coverage Score (0–100)
        - List of top uncited/high-risk claims
        - Suggested minimal patches to add citations/anchors (do not rewrite the whole document)
        If no anchor index is provided, state it clearly and propose an anchor plan.
    """).strip()

    base["WOW AI: Deficiency Draftsmith"]["system_prompt"] = textwrap.dedent("""\
        You are a senior FDA reviewer drafting deficiencies (AI/RAIs).
        Use provided checklist/instructions and sponsor info to draft structured deficiency questions.
        Output Markdown with:
        - Deficiency Title
        - Basis/Reference (quote if available)
        - What was provided
        - What is missing
        - Specific question(s) to sponsor
        - Severity tier (Admin/Scientific/Labeling/Software/Cybersecurity/etc.)
        Do not assume something is required if not stated; differentiate "not found" vs "not required."
    """).strip()

    base["WOW AI: Predicate Differentiator"]["system_prompt"] = textwrap.dedent("""\
        You are a predicate comparison specialist.
        Produce a structured predicate comparison matrix and "So What?" risk implications.
        Output:
        - Comparison Table (Intended Use, Tech, Materials, Performance, SW/Cyber, Labeling)
        - Differentiation Risk Flags (bullet list)
        - Reviewer follow-up checks
        Do not claim substantial equivalence; provide analysis only.
    """).strip()

    # Grok default endpoint tends to be faster; keep OpenAI default though.
    return base


def default_agents_yaml_text() -> str:
    # A minimal, valid starting point; user can replace.
    return textwrap.dedent("""\
    agents:
      - name: Extract Key Device Facts
        description: Extract intended use, indications, key tech characteristics, and likely product codes.
        input: "{input}"
        system_prompt: "You are an FDA 510(k) reviewer. Extract structured device facts in Markdown."
      - name: Build Review Checklist Draft
        description: Draft an initial checklist aligned to typical 510(k) expectations.
        input: "{input}"
        system_prompt: "Draft a reviewer checklist in Markdown [ ] format. Be practical and complete."
      - name: Draft Deficiency Questions
        description: Turn gaps into sponsor questions.
        input: "{input}"
        system_prompt: "Draft concise deficiency questions. Use Markdown headings and bullets."
    """).strip()


# -----------------------------
# Styling (CSS Injection)
# -----------------------------

def build_css(theme: str, pantone_key: str, painter_style: str, reduce_motion: bool) -> str:
    palette = PANTONE_PALETTES.get(pantone_key, list(PANTONE_PALETTES.values())[0])
    accent = palette["accent"]
    accent2 = palette["accent2"]

    is_dark = (theme == "Dark")
    bg = "#0E1117" if is_dark else "#FFFFFF"
    panel = "#111827" if is_dark else "#F7F7FB"
    text = "#E5E7EB" if is_dark else "#111827"
    subtle = "#9CA3AF" if is_dark else "#6B7280"
    border = "#243042" if is_dark else "#E5E7EB"

    # Painter overlay: lightweight gradients/pattern hints
    overlay_map = {
        "Monet Mist": f"linear-gradient(90deg, {accent}18, {accent2}10)",
        "Van Gogh Vortex": f"radial-gradient(circle at 20% 30%, {accent}22, transparent 55%), radial-gradient(circle at 80% 20%, {accent2}18, transparent 50%)",
        "Hokusai Wave": f"linear-gradient(135deg, {accent}14 0%, transparent 60%), linear-gradient(225deg, {accent2}10 0%, transparent 55%)",
        "Klimt Gilded Grid": f"linear-gradient(90deg, {accent}10 1px, transparent 1px), linear-gradient(0deg, {accent2}10 1px, transparent 1px)",
        "Picasso Cubist Panels": f"linear-gradient(120deg, {accent}10 0%, transparent 55%), linear-gradient(300deg, {accent2}10 0%, transparent 60%)",
        "Rothko Color Fields": f"linear-gradient(180deg, {accent}18 0%, transparent 55%), linear-gradient(0deg, {accent2}10 0%, transparent 60%)",
        "Pollock Splatter Trace": f"radial-gradient(circle at 10% 20%, {accent}18 0 2px, transparent 3px), radial-gradient(circle at 70% 40%, {accent2}18 0 2px, transparent 3px)",
        "Vermeer Pearl Light": f"radial-gradient(circle at 30% 30%, {accent}12, transparent 55%)",
        "Rembrandt Shadow Depth": f"linear-gradient(90deg, transparent, {accent2}14)",
        "Turner Atmosphere": f"linear-gradient(135deg, {accent}12, transparent 60%), radial-gradient(circle at 70% 30%, {accent2}10, transparent 55%)",
        "Matisse Cutout Pop": f"linear-gradient(90deg, {accent}12 0 20%, transparent 40%), linear-gradient(90deg, transparent 60%, {accent2}10 80%)",
        "Cézanne Structure": f"linear-gradient(0deg, {accent}10 1px, transparent 1px)",
        "Dalí Surreal Edge": f"linear-gradient(45deg, {accent}12, transparent 55%), linear-gradient(225deg, {accent2}12, transparent 55%)",
        "Kandinsky Geometry": f"radial-gradient(circle at 20% 70%, {accent}12, transparent 45%), radial-gradient(circle at 80% 30%, {accent2}10, transparent 45%)",
        "Frida Botanical Bold": f"linear-gradient(135deg, {accent}14 0%, transparent 55%)",
        "Edward Hopper Quiet Neon": f"linear-gradient(90deg, {accent}10 0%, transparent 60%), linear-gradient(0deg, {accent2}08 0%, transparent 70%)",
        "Georgia O’Keeffe Bloom": f"radial-gradient(circle at 50% 30%, {accent}14, transparent 55%)",
        "Basquiat Neo-Notes": f"linear-gradient(90deg, {accent}10, transparent 40%), radial-gradient(circle at 80% 70%, {accent2}12, transparent 50%)",
        "Magritte Clean Dream": f"linear-gradient(180deg, {accent}08, transparent 70%)",
        "Ink Wash Sumi-e": f"linear-gradient(90deg, {accent2}10, transparent 55%)",
    }
    overlay = overlay_map.get(painter_style, f"linear-gradient(90deg, {accent}10, {accent2}08)")
    motion = "none" if reduce_motion else "all 120ms ease"

    return f"""
    <style>
      :root {{
        --wow-accent: {accent};
        --wow-accent2: {accent2};
        --wow-bg: {bg};
        --wow-panel: {panel};
        --wow-text: {text};
        --wow-subtle: {subtle};
        --wow-border: {border};
      }}

      .stApp {{
        background: var(--wow-bg);
        color: var(--wow-text);
      }}

      /* Header overlay band */
      .wow-header {{
        padding: 12px 14px;
        border: 1px solid var(--wow-border);
        border-radius: 14px;
        background: var(--wow-panel);
        background-image: {overlay};
        margin-bottom: 12px;
      }}

      /* Nordic matte cards */
      .wow-card {{
        padding: 14px 14px;
        border: 1px solid var(--wow-border);
        border-radius: 14px;
        background: var(--wow-panel);
      }}

      /* Accent buttons */
      div.stButton > button {{
        border-radius: 12px !important;
        border: 1px solid var(--wow-border) !important;
        transition: {motion} !important;
      }}
      div.stButton > button:hover {{
        border-color: var(--wow-accent) !important;
        box-shadow: 0 0 0 3px {accent}22 !important;
      }}

      /* Input focus ring */
      textarea:focus, input:focus {{
        outline: none !important;
        box-shadow: 0 0 0 3px {accent}22 !important;
        border-color: var(--wow-accent) !important;
      }}

      /* Indicator chips */
      .wow-chip {{
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid var(--wow-border);
        background: linear-gradient(90deg, {accent}18, transparent);
        color: var(--wow-text);
        font-size: 12px;
        margin-right: 8px;
        margin-bottom: 6px;
      }}
      .wow-chip strong {{
        color: var(--wow-accent);
      }}

      /* Subtle text */
      .wow-muted {{
        color: var(--wow-subtle);
        font-size: 13px;
      }}

      /* Danger zone */
      .wow-danger {{
        border: 1px solid #EF4444;
        background: linear-gradient(90deg, #EF444420, transparent);
      }}
    </style>
    """


# -----------------------------
# Logging & Observability
# -----------------------------

def log_event(level: str, area: str, message: str, meta: Optional[Dict[str, Any]] = None) -> None:
    ss = st.session_state
    if meta is None:
        meta = {}
    # Never log API keys; redact common patterns just in case
    message = redact_secrets(message)
    meta_s = {}
    for k, v in (meta or {}).items():
        if isinstance(v, str):
            meta_s[k] = redact_secrets(v)
        else:
            meta_s[k] = v

    # privacy_mode: reduce risk of storing sensitive user text in logs
    if ss.get("privacy_mode", True):
        if "input_text" in meta_s and isinstance(meta_s["input_text"], str):
            meta_s["input_text_preview"] = safe_preview(meta_s["input_text"])
            meta_s["input_text_len"] = len(meta_s["input_text"])
            del meta_s["input_text"]
        if "output_text" in meta_s and isinstance(meta_s["output_text"], str):
            meta_s["output_text_preview"] = safe_preview(meta_s["output_text"])
            meta_s["output_text_len"] = len(meta_s["output_text"])
            del meta_s["output_text"]

    ss["events"].append({
        "ts": now_taipei_iso(),
        "level": level.upper(),
        "area": area,
        "message": message,
        "meta": meta_s,
        "event_id": uuid4_short(),
    })


def bump_provider_stats(provider: str, ok: bool, latency_ms: int, tokens_in: int, tokens_out: int) -> None:
    ps = st.session_state["provider_stats"].get(provider)
    if not ps:
        return
    ps["calls"] += 1
    if not ok:
        ps["failures"] += 1
    ps["last_latency_ms"] = latency_ms
    ps["tokens_in"] += int(tokens_in or 0)
    ps["tokens_out"] += int(tokens_out or 0)


# -----------------------------
# API Key Handling
# -----------------------------

ENV_KEY_MAP = {
    "OpenAI": "OPENAI_API_KEY",
    "Gemini": "GEMINI_API_KEY",
    "Anthropic": "ANTHROPIC_API_KEY",
    "Grok": "GROK_API_KEY",  # allow user to set; some deployments use XAI_API_KEY
}

ALT_ENV_KEY_MAP = {
    "Grok": ["XAI_API_KEY"],
}


def env_key_present(provider: str) -> bool:
    k = ENV_KEY_MAP.get(provider)
    if k and os.getenv(k):
        return True
    for alt in ALT_ENV_KEY_MAP.get(provider, []):
        if os.getenv(alt):
            return True
    return False


def get_api_key(provider: str) -> Optional[str]:
    # Priority 1: Environment
    k = ENV_KEY_MAP.get(provider)
    if k and os.getenv(k):
        return os.getenv(k)
    for alt in ALT_ENV_KEY_MAP.get(provider, []):
        if os.getenv(alt):
            return os.getenv(alt)

    # Priority 2: Session
    val = st.session_state["api_keys_session"].get(provider, "").strip()
    return val or None


# -----------------------------
# LLM Call Adapters
# -----------------------------

@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    latency_ms: int
    tokens_in: int
    tokens_out: int
    raw: Optional[Dict[str, Any]] = None


def call_llm(provider: str, model: str, system_prompt: str, user_prompt: str,
             max_tokens: int, temperature: float) -> LLMResult:
    """
    Provider-agnostic LLM caller with best-effort implementations and graceful fallbacks.

    Notes on compatibility:
    - OpenAI: uses 'openai' SDK if available; else requests to /chat/completions
    - Grok: uses OpenAI-compatible API via base_url https://api.x.ai/v1 (requests fallback)
    - Anthropic: uses 'anthropic' SDK if available; else requests (if user configured)
    - Gemini: uses google-generativeai if available; else requests fallback (if configured)
    """
    api_key = get_api_key(provider)
    if not api_key:
        raise RuntimeError(f"Missing API key for {provider}. Provide via environment secrets or session input.")

    tokens_in = estimate_tokens(system_prompt) + estimate_tokens(user_prompt)
    t0 = time.time()
    ok = False
    out_text = ""
    raw = None

    try:
        if provider == "OpenAI":
            out_text, raw = call_openai_like(
                base_url="https://api.openai.com/v1",
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "Grok":
            # xAI Grok API is OpenAI-compatible at https://api.x.ai/v1
            out_text, raw = call_openai_like(
                base_url="https://api.x.ai/v1",
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "Anthropic":
            out_text, raw = call_anthropic(
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        elif provider == "Gemini":
            out_text, raw = call_gemini(
                api_key=api_key,
                model=model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        else:
            raise RuntimeError(f"Unsupported provider: {provider}")

        ok = True
        return LLMResult(
            text=(out_text or "").strip(),
            provider=provider,
            model=model,
            latency_ms=int((time.time() - t0) * 1000),
            tokens_in=tokens_in,
            tokens_out=estimate_tokens(out_text),
            raw=raw,
        )

    finally:
        latency = int((time.time() - t0) * 1000)
        bump_provider_stats(provider, ok=ok, latency_ms=latency, tokens_in=tokens_in, tokens_out=estimate_tokens(out_text))
        log_event(
            "INFO" if ok else "ERROR",
            area="LLM",
            message=f"{provider}/{model} call {'OK' if ok else 'FAILED'} ({latency} ms)",
            meta={"provider": provider, "model": model, "latency_ms": latency},
        )


def call_openai_like(base_url: str, api_key: str, model: str,
                     system_prompt: str, user_prompt: str,
                     max_tokens: int, temperature: float) -> Tuple[str, Dict[str, Any]]:
    # Prefer official OpenAI SDK if installed
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI(api_key=api_key, base_url=base_url)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt or ""},
            ],
            temperature=float(temperature),
            max_tokens=int(max_tokens),
        )
        text = resp.choices[0].message.content if resp and resp.choices else ""
        return text or "", {"sdk": "openai", "base_url": base_url}
    except Exception:
        # Fallback to HTTP requests if SDK is missing or fails
        if requests is None:
            raise RuntimeError("requests is not available; cannot call OpenAI-compatible endpoint.")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "messages": [
                {"role": "system", "content": system_prompt or ""},
                {"role": "user", "content": user_prompt or ""},
            ],
        }
        r = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload, timeout=180)
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI-like API error {r.status_code}: {r.text[:500]}")
        data = r.json()
        text = (((data.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""
        return text, {"sdk": "requests", "base_url": base_url, "response_meta": {"id": data.get("id")}}


def call_anthropic(api_key: str, model: str, system_prompt: str, user_prompt: str,
                   max_tokens: int, temperature: float) -> Tuple[str, Dict[str, Any]]:
    try:
        import anthropic  # type: ignore
        client = anthropic.Anthropic(api_key=api_key)
        # Anthropic uses "system" separately; content is list of blocks
        resp = client.messages.create(
            model=model,
            system=system_prompt or "",
            max_tokens=int(max_tokens),
            temperature=float(temperature),
            messages=[{"role": "user", "content": user_prompt or ""}],
        )
        # resp.content is a list of blocks
        text_blocks = []
        for blk in (resp.content or []):
            # blk may be dict-like or object; handle both
            t = getattr(blk, "text", None) or (blk.get("text") if isinstance(blk, dict) else None)
            if t:
                text_blocks.append(t)
        return "\n".join(text_blocks).strip(), {"sdk": "anthropic"}
    except Exception:
        if requests is None:
            raise RuntimeError("Anthropic SDK not available and requests missing; cannot call Anthropic.")
        # Optional fallback: user may provide a custom proxy. Keep disabled by default.
        raise RuntimeError("Anthropic SDK call failed. Install anthropic package or configure a compatible endpoint.")


def call_gemini(api_key: str, model: str, system_prompt: str, user_prompt: str,
                max_tokens: int, temperature: float) -> Tuple[str, Dict[str, Any]]:
    # Try google-generativeai
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)

        # Some Gemini SDK versions do not support system prompts directly per call;
        # emulate by prefixing system instructions.
        merged = (system_prompt.strip() + "\n\n" + user_prompt.strip()).strip() if system_prompt else (user_prompt or "")
        gmodel = genai.GenerativeModel(model)
        resp = gmodel.generate_content(
            merged,
            generation_config={
                "temperature": float(temperature),
                "max_output_tokens": int(max_tokens),
            },
        )
        text = getattr(resp, "text", "") or ""
        return text.strip(), {"sdk": "google-generativeai"}
    except Exception:
        if requests is None:
            raise RuntimeError("Gemini SDK not available and requests missing; cannot call Gemini.")
        raise RuntimeError("Gemini SDK call failed. Install google-generativeai package or configure a compatible endpoint.")


# -----------------------------
# Artifacts (versioning)
# -----------------------------

def save_artifact(name: str, content: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if meta is None:
        meta = {}
    artifacts = st.session_state["artifacts"]
    artifacts.setdefault(name, [])
    version = len(artifacts[name]) + 1
    item = {
        "artifact_id": f"{name}:{uuid4_short()}",
        "name": name,
        "version": version,
        "ts": now_taipei_iso(),
        "content": content or "",
        "meta": meta,
    }
    artifacts[name].append(item)
    log_event("INFO", "Artifact", f"Saved artifact '{name}' v{version}", meta={"artifact": name, "version": version})
    return item


def latest_artifact_text(name: str) -> str:
    items = st.session_state["artifacts"].get(name, [])
    return items[-1]["content"] if items else ""


# -----------------------------
# Validators / Quality Gates
# -----------------------------

def count_markdown_tables(md: str) -> int:
    # Heuristic: count header-separator lines like "|---|---|"
    if not md:
        return 0
    return len(re.findall(r"^\s*\|(?:\s*:?-+:?\s*\|)+\s*$", md, flags=re.MULTILINE))


def has_checklist(md: str) -> bool:
    if not md:
        return False
    return bool(re.search(r"^\s*[-*]?\s*\[\s*\]\s+.+$", md, flags=re.MULTILINE))


def structural_warnings_for_step(step: int, text: str) -> List[str]:
    warns = []
    wc = word_count(text)
    if step == 1 and not (2000 <= wc <= 3000):
        warns.append(f"Step 1 word count out of range: {wc} (expected 2000–3000).")
    if step == 2:
        if not (2000 <= wc <= 3000):
            warns.append(f"Step 2 word count out of range: {wc} (expected 2000–3000).")
        tcount = count_markdown_tables(text)
        if tcount != 3:
            warns.append(f"Step 2 table count is {tcount} (expected EXACTLY 3).")
        if not has_checklist(text):
            warns.append("Step 2 checklist not detected (expected Markdown [ ] checklist).")
    if step == 4 and not (3000 <= wc <= 4000):
        warns.append(f"Step 4 word count out of range: {wc} (expected 3000–4000).")
    return warns


# -----------------------------
# UI Components
# -----------------------------

def dual_view_editor(key: str, label: str, value: str, height: int = 240) -> str:
    col1, col2 = st.columns([1, 1], vertical_alignment="top")
    with col1:
        edited = st.text_area(label, value=value or "", key=f"{key}_edit", height=height)
    with col2:
        st.markdown("**Preview (Markdown Render)**")
        st.markdown(edited or "")
    return edited


def indicator_row(step_key: str, text: str, provider: str, model: str, max_tokens: int) -> None:
    wc = word_count(text)
    tok = estimate_tokens(text)
    ps = st.session_state["provider_stats"].get(provider, {})
    latency = ps.get("last_latency_ms")

    chips = []
    chips.append(f"<span class='wow-chip'><strong>Words</strong> {wc}</span>")
    chips.append(f"<span class='wow-chip'><strong>Est. Tokens</strong> {tok}</span>")
    chips.append(f"<span class='wow-chip'><strong>Max Tokens</strong> {int(max_tokens)}</span>")
    if latency is not None:
        chips.append(f"<span class='wow-chip'><strong>Last Latency</strong> {latency} ms</span>")
    chips.append(f"<span class='wow-chip'><strong>Model</strong> {provider}/{model}</span>")

    st.markdown("".join(chips), unsafe_allow_html=True)

    # Lightweight warnings for token pressure
    if tok > 120_000:
        st.warning("High context size detected. Consider trimming input or using a larger-context model.")


def api_keys_panel(lang: str) -> None:
    t = I18N[lang]
    st.subheader(t["api_keys"])
    st.caption("Environment keys are preferred. If not detected, enter session keys (masked). Never logged.")

    for provider in ["OpenAI", "Gemini", "Anthropic", "Grok"]:
        with st.container(border=True):
            st.markdown(f"**{provider}**")
            if env_key_present(provider):
                st.info(t["managed_by_system"])
            else:
                st.text_input(
                    f"{provider} API Key (session-only)",
                    type="password",
                    key=f"key_{provider}",
                    value=st.session_state["api_keys_session"].get(provider, ""),
                    on_change=lambda p=provider: _sync_key_input(p),
                    help="Stored in Streamlit session_state only. Cleared by Total Purge.",
                )


def _sync_key_input(provider: str) -> None:
    st.session_state["api_keys_session"][provider] = st.session_state.get(f"key_{provider}", "")


def settings_matrix_ui() -> None:
    st.subheader(I18N[st.session_state["lang"]]["settings_matrix"])
    st.caption("Configure provider/model/prompt per feature. Defaults target max_tokens=12000.")

    ss = st.session_state
    matrix = ss["settings_matrix"]

    feature = st.selectbox("Select Feature", options=list(matrix.keys()))
    cfg = matrix[feature]

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        provider = st.selectbox("Provider", options=list(MODEL_CATALOG.keys()), index=list(MODEL_CATALOG.keys()).index(cfg["provider"]))
    with c2:
        models = MODEL_CATALOG.get(provider, [])
        default_model = cfg["model"] if cfg["model"] in models else (models[0] if models else cfg["model"])
        model = st.selectbox("Model", options=models + (["(custom)"] if cfg["model"] not in models else []), index=(models.index(default_model) if default_model in models else len(models)))
    with c3:
        strict = st.toggle("Strict Regulatory Tone", value=bool(cfg.get("strict_tone", True)))

    if model == "(custom)":
        model = st.text_input("Custom model name", value=cfg["model"])

    system_prompt = st.text_area("System Prompt", value=cfg["system_prompt"], height=180)
    user_tmpl = st.text_area("User Prompt Template (use {input})", value=cfg["user_prompt_template"], height=110)

    c4, c5, c6 = st.columns([1, 1, 1])
    with c4:
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=float(cfg["temperature"]), step=0.05)
    with c5:
        max_tokens = st.number_input("Max tokens", min_value=256, max_value=200000, value=int(cfg.get("max_tokens", DEFAULT_MAX_TOKENS)), step=256)
    with c6:
        output_format = st.selectbox("Output format preference", options=["Markdown", "Text", "JSON"], index=["Markdown", "Text", "JSON"].index(cfg.get("output_format", "Markdown")))

    if st.button("Save Settings", type="primary"):
        matrix[feature] = {
            "provider": provider,
            "model": model,
            "system_prompt": system_prompt,
            "user_prompt_template": user_tmpl,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "output_format": output_format,
            "strict_tone": bool(strict),
        }
        log_event("INFO", "Settings", f"Saved settings for feature: {feature}", meta={"feature": feature, "provider": provider, "model": model})
        st.success("Saved.")

    with st.expander("Export / Import Settings"):
        c7, c8 = st.columns([1, 1])
        with c7:
            settings_json = json.dumps(matrix, indent=2, ensure_ascii=False)
            st.download_button("Download settings.json", data=settings_json, file_name="settings.json", mime="application/json")
        with c8:
            up = st.file_uploader("Upload settings.json", type=["json"], accept_multiple_files=False, key="settings_upload")
            if up is not None:
                try:
                    loaded = json.loads(up.read().decode("utf-8"))
                    if isinstance(loaded, dict):
                        ss["settings_matrix"] = loaded
                        log_event("INFO", "Settings", "Imported settings.json")
                        st.success("Imported.")
                    else:
                        st.error("Invalid settings file format.")
                except Exception as e:
                    st.error(f"Failed to import: {e}")


# -----------------------------
# OCR / Ingestion (Lightweight)
# -----------------------------

def upload_and_ocr_ui() -> None:
    st.subheader("Ingestion & Extraction (Legacy Retained)")
    st.caption("Upload PDFs. Use Python extraction as baseline. LLM OCR is specified but not implemented in this single-file demo.")

    uploads = st.file_uploader("Upload PDF(s)", type=["pdf"], accept_multiple_files=True)
    if uploads:
        for f in uploads:
            b = f.read()
            st.session_state["uploads"].append({"name": f.name, "bytes": b, "size": len(b)})
            log_event("INFO", "Ingestion", "Uploaded file", meta={"filename": f.name, "bytes": len(b)})

    if st.session_state["uploads"]:
        st.markdown("### File Queue")
        for i, u in enumerate(st.session_state["uploads"]):
            with st.container(border=True):
                st.markdown(f"**{i+1}. {u['name']}**  \n<span class='wow-muted'>Size: {u['size']} bytes</span>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button("Python Extract Text", key=f"pyocr_{i}"):
                        text = python_pdf_extract(u["bytes"], u["name"])
                        st.session_state["ocr_text_by_file"][u["name"]] = text
                        save_artifact(f"OCR:{u['name']}", text, meta={"method": "PyPDF2" if PdfReader else "Unavailable"})
                        st.success("Extracted.")
                with c2:
                    if st.button("Clear from Queue", key=f"clr_{i}"):
                        st.session_state["uploads"].pop(i)
                        st.rerun()

        st.markdown("### OCR Outputs")
        for fname, text in st.session_state["ocr_text_by_file"].items():
            with st.expander(f"OCR: {fname}", expanded=False):
                st.text_area("Extracted text", value=text, height=180, key=f"ocr_view_{fname}")
                st.download_button("Download .txt", data=text, file_name=f"{fname}.txt", mime="text/plain")


def python_pdf_extract(pdf_bytes: bytes, filename: str) -> str:
    if PdfReader is None:
        log_event("ERROR", "OCR", "PyPDF2 not installed; cannot extract.", meta={"filename": filename})
        return "ERROR: PyPDF2 not installed. Please add PyPDF2 to requirements."
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        out = "\n\n".join(pages).strip()
        if not out:
            out = "WARNING: No extractable text found (PDF may be scanned). Consider LLM OCR pipeline."
        log_event("INFO", "OCR", "Python PDF text extracted", meta={"filename": filename, "chars": len(out)})
        return out
    except Exception as e:
        log_event("ERROR", "OCR", "Python extraction failed", meta={"filename": filename, "error": str(e)})
        return f"ERROR: Extraction failed: {e}"


# -----------------------------
# Pipeline Execution
# -----------------------------

def run_feature_llm(feature_key: str, input_text: str, extra_context: Optional[Dict[str, str]] = None) -> str:
    cfg = st.session_state["settings_matrix"][feature_key]
    provider = cfg["provider"]
    model = cfg["model"]
    system_prompt = cfg["system_prompt"]
    temperature = float(cfg["temperature"])
    max_tokens = int(cfg["max_tokens"])

    tmpl = cfg.get("user_prompt_template", "{input}") or "{input}"
    merged_input = input_text or ""
    if extra_context:
        # Add context as a structured preface to reduce prompt injection risk
        ctx_parts = []
        for k, v in extra_context.items():
            ctx_parts.append(f"## CONTEXT: {k}\n{v}\n")
        merged_input = "\n\n".join(ctx_parts) + "\n\n## USER INPUT\n" + merged_input

    user_prompt = tmpl.replace("{input}", merged_input)

    log_event("INFO", "Preflight", f"Running {feature_key}", meta={
        "feature": feature_key,
        "provider": provider,
        "model": model,
        "tokens_est_in": estimate_tokens(system_prompt) + estimate_tokens(user_prompt),
    })

    res = call_llm(
        provider=provider,
        model=model,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return res.text


def pipeline_ui() -> None:
    st.subheader("4-Step Intelligent Review Generation Pipeline (v3.1)")

    p = st.session_state["pipeline"]
    status = p["status"]

    # Step 1
    with st.container(border=True):
        st.markdown("## Step 1 — Device Context & FDA Intelligence Summary (2000–3000 words)")
        cfg = st.session_state["settings_matrix"]["Pipeline Step 1: FDA Intelligence Summary"]
        indicator_row("step1", p["step1_output"], cfg["provider"], cfg["model"], cfg["max_tokens"])
        p["step1_input"] = st.text_area("Paste device information (text/markdown)", value=p["step1_input"], height=160, key="step1_in")
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Run Step 1", type="primary"):
                try:
                    out = run_feature_llm("Pipeline Step 1: FDA Intelligence Summary", p["step1_input"])
                    p["step1_output"] = out
                    status["step1"] = "Complete"
                    save_artifact("Pipeline Step 1 Output", out, meta={"provider": cfg["provider"], "model": cfg["model"]})
                    st.success("Generated Step 1 output.")
                except Exception as e:
                    status["step1"] = "Error"
                    log_event("ERROR", "Pipeline", "Step 1 failed", meta={"error": str(e)})
                    st.error(str(e))
        with c2:
            if st.button("Load OCR into Step 1"):
                # Merge all OCR outputs into input
                merged = "\n\n".join(st.session_state["ocr_text_by_file"].values())
                p["step1_input"] = (p["step1_input"] + "\n\n" + merged).strip()
                st.rerun()
        with c3:
            st.markdown(f"<span class='wow-muted'>Status: {status['step1']}</span>", unsafe_allow_html=True)

        if p["step1_output"]:
            edited = dual_view_editor("step1_out", "Step 1 Output (editable)", p["step1_output"], height=220)
            p["step1_output"] = edited
            warns = structural_warnings_for_step(1, edited)
            for w in warns:
                st.warning(w)
            st.download_button("Download Step 1 (.md)", data=edited, file_name="step1_device_intelligence.md", mime="text/markdown")

    # Step 2
    with st.container(border=True):
        st.markdown("## Step 2 — Guidance-Driven Review Instructions (2000–3000 words, checklist + exactly 3 tables)")
        cfg = st.session_state["settings_matrix"]["Pipeline Step 2: Guidance Review Instructions"]
        indicator_row("step2", p["step2_output"], cfg["provider"], cfg["model"], cfg["max_tokens"])
        p["step2_input"] = st.text_area("Paste guidance (text/markdown) or extracted OCR", value=p["step2_input"], height=160, key="step2_in")

        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Run Step 2", type="primary"):
                if status["step1"] != "Complete" or not p["step1_output"].strip():
                    st.error("Step 1 must be completed before Step 2.")
                else:
                    try:
                        out = run_feature_llm(
                            "Pipeline Step 2: Guidance Review Instructions",
                            p["step2_input"],
                            extra_context={"Step 1 Device Intelligence Summary": p["step1_output"]},
                        )
                        p["step2_output"] = out
                        status["step2"] = "Complete"
                        save_artifact("Pipeline Step 2 Output", out, meta={"provider": cfg["provider"], "model": cfg["model"]})
                        st.success("Generated Step 2 output.")
                    except Exception as e:
                        status["step2"] = "Error"
                        log_event("ERROR", "Pipeline", "Step 2 failed", meta={"error": str(e)})
                        st.error(str(e))
        with c2:
            if st.button("Load OCR into Step 2"):
                merged = "\n\n".join(st.session_state["ocr_text_by_file"].values())
                p["step2_input"] = (p["step2_input"] + "\n\n" + merged).strip()
                st.rerun()
        with c3:
            st.markdown(f"<span class='wow-muted'>Status: {status['step2']}</span>", unsafe_allow_html=True)

        if p["step2_output"]:
            edited = dual_view_editor("step2_out", "Step 2 Output (editable)", p["step2_output"], height=220)
            p["step2_output"] = edited
            warns = structural_warnings_for_step(2, edited)
            for w in warns:
                st.warning(w)
            st.download_button("Download Step 2 (.md)", data=edited, file_name="step2_guidance_instructions.md", mime="text/markdown")

    # Step 3
    with st.container(border=True):
        st.markdown("## Step 3 — Submission Summary Reorganization")
        cfg = st.session_state["settings_matrix"]["Pipeline Step 3: Submission Reorganization"]
        indicator_row("step3", p["step3_output"], cfg["provider"], cfg["model"], cfg["max_tokens"])
        p["step3_input"] = st.text_area("Paste sponsor submission summary (text/markdown)", value=p["step3_input"], height=160, key="step3_in")
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1:
            if st.button("Run Step 3", type="primary"):
                if status["step2"] != "Complete" or not p["step2_output"].strip():
                    st.error("Step 2 must be completed before Step 3.")
                else:
                    try:
                        out = run_feature_llm(
                            "Pipeline Step 3: Submission Reorganization",
                            p["step3_input"],
                            extra_context={"Step 2 Review Instructions": p["step2_output"]},
                        )
                        p["step3_output"] = out
                        status["step3"] = "Complete"
                        save_artifact("Pipeline Step 3 Output", out, meta={"provider": cfg["provider"], "model": cfg["model"]})
                        st.success("Generated Step 3 output.")
                    except Exception as e:
                        status["step3"] = "Error"
                        log_event("ERROR", "Pipeline", "Step 3 failed", meta={"error": str(e)})
                        st.error(str(e))
        with c2:
            if st.button("Load OCR into Step 3"):
                merged = "\n\n".join(st.session_state["ocr_text_by_file"].values())
                p["step3_input"] = (p["step3_input"] + "\n\n" + merged).strip()
                st.rerun()
        with c3:
            st.markdown(f"<span class='wow-muted'>Status: {status['step3']}</span>", unsafe_allow_html=True)

        if p["step3_output"]:
            edited = dual_view_editor("step3_out", "Step 3 Output (editable)", p["step3_output"], height=220)
            p["step3_output"] = edited
            st.download_button("Download Step 3 (.md)", data=edited, file_name="step3_reorganized_submission.md", mime="text/markdown")

    # Step 4
    with st.container(border=True):
        st.markdown("## Step 4 — Final Comprehensive Review Report (3000–4000 words)")
        cfg = st.session_state["settings_matrix"]["Pipeline Step 4: Final Comprehensive Review"]
        indicator_row("step4", p["step4_output"], cfg["provider"], cfg["model"], cfg["max_tokens"])
        p["step4_input"] = st.text_area("Optional reviewer instructions for the final report", value=p["step4_input"], height=120, key="step4_in")
        c1, c2 = st.columns([1, 2])
        with c1:
            if st.button("Run Step 4", type="primary"):
                if status["step3"] != "Complete" or not p["step3_output"].strip():
                    st.error("Step 3 must be completed before Step 4.")
                else:
                    try:
                        out = run_feature_llm(
                            "Pipeline Step 4: Final Comprehensive Review",
                            p["step4_input"],
                            extra_context={
                                "Step 1 Device Intelligence Summary": p["step1_output"],
                                "Step 2 Review Instructions": p["step2_output"],
                                "Step 3 Reorganized Submission": p["step3_output"],
                            },
                        )
                        p["step4_output"] = out
                        status["step4"] = "Complete"
                        save_artifact("Pipeline Step 4 Output", out, meta={"provider": cfg["provider"], "model": cfg["model"]})
                        st.success("Generated Step 4 output.")
                    except Exception as e:
                        status["step4"] = "Error"
                        log_event("ERROR", "Pipeline", "Step 4 failed", meta={"error": str(e)})
                        st.error(str(e))
        with c2:
            st.markdown(f"<span class='wow-muted'>Status: {status['step4']}</span>", unsafe_allow_html=True)

        if p["step4_output"]:
            edited = dual_view_editor("step4_out", "Step 4 Output (editable)", p["step4_output"], height=260)
            p["step4_output"] = edited
            warns = structural_warnings_for_step(4, edited)
            for w in warns:
                st.warning(w)
            st.download_button("Download Step 4 (.md)", data=edited, file_name="step4_final_review_report.md", mime="text/markdown")


# -----------------------------
# Agents Runner (agents.yaml)
# -----------------------------

def parse_agents_yaml(text: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if yaml is None:
        return None, "pyyaml not installed. Add pyyaml to requirements."
    try:
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict) or "agents" not in data or not isinstance(data["agents"], list):
            return None, "Invalid agents.yaml format. Must be a mapping with key 'agents' as a list."
        for a in data["agents"]:
            if not isinstance(a, dict) or "name" not in a:
                return None, "Each agent must be a mapping with at least a 'name'."
            a.setdefault("system_prompt", "You are a helpful agent.")
            a.setdefault("input", "{input}")
            a.setdefault("description", "")
        return data, None
    except Exception as e:
        return None, f"YAML parse error: {e}"


def agents_runner_ui() -> None:
    st.subheader("Agents Runner (Step-by-Step, Human-in-the-Loop)")

    c1, c2 = st.columns([1, 1])
    with c1:
        st.session_state["agents_yaml_text"] = st.text_area(
            "agents.yaml (editable)",
            value=st.session_state["agents_yaml_text"],
            height=240,
            key="agents_yaml_editor",
        )
    with c2:
        st.markdown("**Working Chain Input (editable)**")
        st.session_state["agent_chain_input"] = st.text_area(
            "This text will be used as {input} for the selected agent.",
            value=st.session_state["agent_chain_input"] or st.session_state["pipeline"].get("step3_output", ""),
            height=240,
            key="agent_chain_input_editor",
        )

    if st.button("Validate agents.yaml"):
        parsed, err = parse_agents_yaml(st.session_state["agents_yaml_text"])
        if err:
            st.error(err)
            log_event("ERROR", "Agents", "agents.yaml validation failed", meta={"error": err})
        else:
            st.session_state["agents_parsed"] = parsed
            st.success("agents.yaml is valid.")
            log_event("INFO", "Agents", "agents.yaml validated")

    parsed = st.session_state.get("agents_parsed")
    if not parsed:
        parsed, err = parse_agents_yaml(st.session_state["agents_yaml_text"])
        if not err:
            st.session_state["agents_parsed"] = parsed

    if not st.session_state.get("agents_parsed"):
        st.info("Validate agents.yaml to run agents.")
        return

    agents = st.session_state["agents_parsed"]["agents"]
    names = [a["name"] for a in agents]
    idx = st.selectbox("Select agent", options=list(range(len(names))), format_func=lambda i: names[i])
    agent = agents[idx]

    st.markdown(f"**Description:** {agent.get('description','') or '—'}")

    # Per-agent overrides before execution
    with st.expander("Pre-Run Controls (Prompt / Model / Max Tokens)", expanded=True):
        feature_key = "Agents Runner: Default"
        cfg_base = st.session_state["settings_matrix"][feature_key].copy()

        cA, cB, cC = st.columns([1, 1, 1])
        with cA:
            provider = st.selectbox("Provider", options=list(MODEL_CATALOG.keys()), index=list(MODEL_CATALOG.keys()).index(cfg_base["provider"]), key=f"agent_provider_{idx}")
        with cB:
            models = MODEL_CATALOG.get(provider, [])
            model = st.selectbox("Model", options=models, index=0, key=f"agent_model_{idx}")
        with cC:
            max_tokens = st.number_input("Max tokens", min_value=256, max_value=200000, value=int(cfg_base.get("max_tokens", DEFAULT_MAX_TOKENS)), step=256, key=f"agent_maxtok_{idx}")

        temperature = st.slider("Temperature", 0.0, 1.0, float(cfg_base.get("temperature", 0.2)), 0.05, key=f"agent_temp_{idx}")

        sys_prompt = st.text_area("System prompt (agent-level)", value=agent.get("system_prompt", ""), height=140, key=f"agent_sysp_{idx}")
        input_tmpl = st.text_area("Input template (use {input})", value=agent.get("input", "{input}"), height=80, key=f"agent_intmpl_{idx}")

    # Execute
    if st.button("Run Selected Agent", type="primary"):
        try:
            chain_input = st.session_state["agent_chain_input"] or ""
            user_prompt = (input_tmpl or "{input}").replace("{input}", chain_input)

            res = call_llm(
                provider=provider,
                model=model,
                system_prompt=sys_prompt,
                user_prompt=user_prompt,
                max_tokens=int(max_tokens),
                temperature=float(temperature),
            )
            run_id = uuid4_short()
            out = res.text

            st.session_state["agent_runs"].append({
                "run_id": run_id,
                "ts": now_taipei_iso(),
                "agent_name": agent["name"],
                "provider": provider,
                "model": model,
                "temperature": float(temperature),
                "max_tokens": int(max_tokens),
                "input_len": len(chain_input),
                "output_len": len(out),
                "output": out,
            })
            save_artifact(f"Agent:{agent['name']}", out, meta={"provider": provider, "model": model, "run_id": run_id})
            st.success(f"Agent run complete (run_id={run_id}).")
        except Exception as e:
            log_event("ERROR", "Agents", "Agent run failed", meta={"error": str(e), "agent": agent.get("name")})
            st.error(str(e))

    # Run history + post-edit commit
    if st.session_state["agent_runs"]:
        st.markdown("### Agent Runs (History)")
        for r_i in reversed(range(len(st.session_state["agent_runs"]))):
            r = st.session_state["agent_runs"][r_i]
            with st.expander(f"{r['ts']} — {r['agent_name']} — {r['provider']}/{r['model']} — run_id={r['run_id']}", expanded=False):
                edited = dual_view_editor(f"agent_run_{r['run_id']}", "Output (editable; commit to next agent)", r["output"], height=220)
                st.session_state["agent_runs"][r_i]["output"] = edited

                cX, cY, cZ = st.columns([1, 1, 1])
                with cX:
                    if st.button("Commit as Chain Input", key=f"commit_{r['run_id']}"):
                        st.session_state["agent_chain_input"] = edited
                        log_event("INFO", "Agents", "Committed agent output as chain input", meta={"run_id": r["run_id"], "agent": r["agent_name"]})
                        st.success("Committed.")
                        st.rerun()
                with cY:
                    st.download_button("Download (.md)", data=edited, file_name=f"agent_{r['agent_name']}_{r['run_id']}.md", mime="text/markdown")
                with cZ:
                    if st.button("Fork Version (save artifact)", key=f"fork_{r['run_id']}"):
                        save_artifact(f"Agent:{r['agent_name']}", edited, meta={"forked_from": r["run_id"], "provider": r["provider"], "model": r["model"]})
                        st.success("Forked as new artifact version.")


# -----------------------------
# WOW AI Suite UI
# -----------------------------

def wow_ai_ui() -> None:
    st.subheader("WOW AI Suite (8 Modules)")

    # Choose target artifact
    artifact_names = list(st.session_state["artifacts"].keys())
    target = st.selectbox("Select target artifact", options=(artifact_names or ["(none)"]))
    if not artifact_names:
        st.info("No artifacts yet. Run pipeline steps or agents first.")
        return

    target_text = latest_artifact_text(target)

    st.markdown("### Quick Indicators")
    st.markdown(
        f"<span class='wow-chip'><strong>Artifact</strong> {target}</span>"
        f"<span class='wow-chip'><strong>Words</strong> {word_count(target_text)}</span>"
        f"<span class='wow-chip'><strong>Est. Tokens</strong> {estimate_tokens(target_text)}</span>",
        unsafe_allow_html=True,
    )

    modules = [
        ("WOW AI: Evidence Mapper", "Run Evidence Mapper"),
        ("WOW AI: Consistency Guardian", "Run Consistency Guardian"),
        ("WOW AI: Regulatory Risk Radar", "Run Regulatory Risk Radar"),
        ("WOW AI: RTA Gatekeeper", "Run RTA Gatekeeper"),
        ("WOW AI: Labeling & Claims Inspector", "Run Labeling & Claims Inspector"),
        ("WOW AI: Citation Sentinel", "Run Citation Sentinel (NEW)"),
        ("WOW AI: Deficiency Draftsmith", "Run Deficiency Draftsmith (NEW)"),
        ("WOW AI: Predicate Differentiator", "Run Predicate Differentiator (NEW)"),
    ]

    st.markdown("### Run Module")
    sel = st.selectbox("Module", options=[m[0] for m in modules])
    btn_label = dict(modules)[sel]

    # Optional context bundle
    extra_ctx = {
        "Pipeline Step 1 Output": st.session_state["pipeline"].get("step1_output", ""),
        "Pipeline Step 2 Output": st.session_state["pipeline"].get("step2_output", ""),
        "Pipeline Step 3 Output": st.session_state["pipeline"].get("step3_output", ""),
        "Pipeline Step 4 Output": st.session_state["pipeline"].get("step4_output", ""),
    }
    # Keep only non-empty
    extra_ctx = {k: v for k, v in extra_ctx.items() if (v or "").strip()}

    if st.button(btn_label, type="primary"):
        try:
            out = run_feature_llm(sel, target_text, extra_context={"Target Artifact": target_text, **extra_ctx})
            save_artifact(f"{sel} Output", out, meta={"target": target, "module": sel})
            st.success("Module completed.")
        except Exception as e:
            log_event("ERROR", "WOW-AI", "Module failed", meta={"module": sel, "error": str(e)})
            st.error(str(e))

    # Show latest module outputs
    st.markdown("### Module Outputs (Latest)")
    for name in list(st.session_state["artifacts"].keys()):
        if name.endswith(" Output") and any(name.startswith(m[0]) for m in modules):
            latest = latest_artifact_text(name)
            with st.expander(name, expanded=False):
                st.markdown(latest or "")
                st.download_button("Download (.md)", data=latest, file_name=f"{name}.md".replace(" ", "_"), mime="text/markdown")


# -----------------------------
# WOW Visualizations
# -----------------------------

def wow_dashboard_ui() -> None:
    t = I18N[st.session_state["lang"]]
    st.subheader(t["dashboard"])

    p = st.session_state["pipeline"]
    status = p["status"]

    # Progress rings (Streamlit: progress bars + metrics)
    st.markdown("### Pipeline Progress")
    cols = st.columns(4)
    steps = [("step1", "Step 1"), ("step2", "Step 2"), ("step3", "Step 3"), ("step4", "Step 4")]
    for i, (k, label) in enumerate(steps):
        with cols[i]:
            val = 1.0 if status[k] == "Complete" else (0.5 if status[k] == "Pending" else 0.2)
            st.progress(val, text=f"{label}: {status[k]}")

    st.markdown("### Provider Telemetry")
    ps = st.session_state["provider_stats"]
    for provider, stats in ps.items():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric(f"{provider} Calls", stats["calls"])
            with c2:
                st.metric("Failures", stats["failures"])
            with c3:
                st.metric("Last Latency (ms)", stats["last_latency_ms"] if stats["last_latency_ms"] is not None else "—")
            with c4:
                st.metric("Tokens In/Out", f"{stats['tokens_in']}/{stats['tokens_out']}")

    st.markdown("### Artifact Lineage (Simplified DAG)")
    # Minimal DAG view: list key artifacts in expected order with latest version
    order = [
        "Pipeline Step 1 Output",
        "Pipeline Step 2 Output",
        "Pipeline Step 3 Output",
        "Pipeline Step 4 Output",
    ]
    for name in order:
        items = st.session_state["artifacts"].get(name, [])
        if not items:
            st.write(f"- {name}: (none)")
            continue
        last = items[-1]
        st.write(f"- {name}: v{last['version']} @ {last['ts']} — {safe_preview(last['content'], 120)}")

    st.markdown("### Quality Gates (Structural)")
    if p.get("step2_output"):
        table_count = count_markdown_tables(p["step2_output"])
        checklist_ok = has_checklist(p["step2_output"])
        st.write(f"- Step 2 Tables: {table_count} (expected 3)")
        st.write(f"- Step 2 Checklist Detected: {'Yes' if checklist_ok else 'No'}")
    if p.get("step4_output"):
        wc4 = word_count(p["step4_output"])
        st.write(f"- Step 4 Word Count: {wc4} (expected 3000–4000)")


def wow_logs_ui() -> None:
    t = I18N[st.session_state["lang"]]
    st.subheader(t["logs"])

    events = st.session_state["events"]
    if not events:
        st.info("No events yet.")
        return

    # Filters
    levels = sorted({e["level"] for e in events})
    areas = sorted({e["area"] for e in events})

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        level_sel = st.multiselect("Level", options=levels, default=levels)
    with c2:
        area_sel = st.multiselect("Area", options=areas, default=areas)
    with c3:
        keyword = st.text_input("Keyword filter", value="")

    st.toggle("Privacy Mode (reduce stored previews)", value=bool(st.session_state["privacy_mode"]), key="privacy_mode")

    filtered = []
    for e in events:
        if e["level"] not in level_sel:
            continue
        if e["area"] not in area_sel:
            continue
        blob = (e["message"] + " " + json.dumps(e["meta"], ensure_ascii=False)).lower()
        if keyword.strip() and keyword.lower() not in blob:
            continue
        filtered.append(e)

    st.caption(f"Showing {len(filtered)} / {len(events)} events. Timezone: {TZ_NAME}.")

    # "Log Theater" view
    for e in reversed(filtered[-200:]):  # cap rendering
        with st.container(border=True):
            st.markdown(
                f"**[{e['level']}]** {e['ts']} — **{e['area']}** — {e['message']}  \n"
                f"<span class='wow-muted'>event_id={e['event_id']}</span>",
                unsafe_allow_html=True,
            )
            if e.get("meta"):
                st.json(e["meta"], expanded=False)

    with st.expander("Export logs.json"):
        st.download_button("Download logs.json", data=json.dumps(events, indent=2, ensure_ascii=False), file_name="logs.json", mime="application/json")


# -----------------------------
# Personalization Header
# -----------------------------

def personalization_header() -> None:
    ss = st.session_state
    lang = ss["lang"]
    t = I18N[lang]

    st.markdown(
        f"<div class='wow-header'>"
        f"<div style='display:flex; gap:10px; align-items:center; justify-content:space-between;'>"
        f"<div><div style='font-size:18px; font-weight:700;'>{t['app_title']}</div>"
        f"<div class='wow-muted'>Pantone × Painter Atelier • Jackpot Edition • HF Spaces • {TZ_NAME}</div></div>"
        f"</div></div>",
        unsafe_allow_html=True
    )

    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 2, 1])
    with c1:
        ss["theme"] = st.selectbox("Theme", THEMES, index=THEMES.index(ss["theme"]))
    with c2:
        ss["lang"] = st.selectbox("Language", LANGS, index=LANGS.index(ss["lang"]))
    with c3:
        ss["pantone"] = st.selectbox("Pantone Accent", list(PANTONE_PALETTES.keys()), index=list(PANTONE_PALETTES.keys()).index(ss["pantone"]))
    with c4:
        ss["painter_style"] = st.selectbox("Painter Style", PAINTER_STYLES, index=PAINTER_STYLES.index(ss["painter_style"]))
    with c5:
        if st.button("Jackpot", type="primary"):
            ss["painter_style"] = random.choice(PAINTER_STYLES)
            log_event("INFO", "UI", "Jackpot painter style selected", meta={"painter_style": ss["painter_style"]})
            st.rerun()

    ss["reduce_motion"] = st.toggle("Reduce Motion", value=bool(ss["reduce_motion"]))


# -----------------------------
# Danger Zone
# -----------------------------

def total_purge_ui() -> None:
    t = I18N[st.session_state["lang"]]
    st.subheader(t["danger_zone"])
    st.warning("This will delete all uploaded files, OCR buffers, artifacts, logs, and session API keys.")
    with st.container(border=True):
        st.markdown("<div class='wow-card wow-danger'>", unsafe_allow_html=True)
        confirm = st.checkbox("I understand this will wipe the current session.")
        if st.button(t["total_purge"], disabled=not confirm):
            # Preserve personalization optionally
            theme = st.session_state["theme"]
            lang = st.session_state["lang"]
            pantone = st.session_state["pantone"]
            painter = st.session_state["painter_style"]
            reduce_motion = st.session_state["reduce_motion"]

            st.session_state.clear()
            init_state()

            st.session_state["theme"] = theme
            st.session_state["lang"] = lang
            st.session_state["pantone"] = pantone
            st.session_state["painter_style"] = painter
            st.session_state["reduce_motion"] = reduce_motion

            log_event("SECURITY", "Purge", "Total Purge executed")
            st.success("Session wiped.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# -----------------------------
# Main App
# -----------------------------

def main() -> None:
    st.set_page_config(
        page_title="FDA 510(k) Review Studio v3.1",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    init_state()

    # Apply CSS
    css = build_css(
        theme=st.session_state["theme"],
        pantone_key=st.session_state["pantone"],
        painter_style=st.session_state["painter_style"],
        reduce_motion=bool(st.session_state["reduce_motion"]),
    )
    st.markdown(css, unsafe_allow_html=True)

    personalization_header()

    lang = st.session_state["lang"]
    t = I18N[lang]

    with st.sidebar:
        st.title(t["sidebar_title"])
        st.caption("All data is ephemeral unless downloaded. Use Total Purge to wipe session immediately.")

        api_keys_panel(lang)

        st.divider()
        st.markdown("### Navigation")
        page = st.radio(
            "Go to",
            options=[
                "Pipeline",
                "Ingestion & OCR",
                "Agents Runner",
                "WOW AI Suite",
                "Settings Matrix",
                "WOW Dashboard",
                "WOW Logs",
                "Danger Zone",
            ],
            index=0,
        )

    if page == "Pipeline":
        pipeline_ui()
    elif page == "Ingestion & OCR":
        upload_and_ocr_ui()
    elif page == "Agents Runner":
        agents_runner_ui()
    elif page == "WOW AI Suite":
        wow_ai_ui()
    elif page == "Settings Matrix":
        settings_matrix_ui()
    elif page == "WOW Dashboard":
        wow_dashboard_ui()
    elif page == "WOW Logs":
        wow_logs_ui()
    elif page == "Danger Zone":
        total_purge_ui()

    # Footer: quick status indicator line
    st.divider()
    ps = st.session_state["provider_stats"]
    total_calls = sum(v["calls"] for v in ps.values())
    total_fail = sum(v["failures"] for v in ps.values())
    st.markdown(
        f"<span class='wow-chip'><strong>Session</strong> {now_taipei_iso()}</span>"
        f"<span class='wow-chip'><strong>Calls</strong> {total_calls}</span>"
        f"<span class='wow-chip'><strong>Failures</strong> {total_fail}</span>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
