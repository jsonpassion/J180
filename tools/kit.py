"""Shared helpers for the vocabulary content kit (config, files, scripts).

Every sister-app content repo carries the same tools; only
content.config.json, plan/curriculum.json and the prompt rules differ.
"""

import json
import os
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "content.config.json").read_text(encoding="utf-8"))
PLAN_DIR = ROOT / "plan"

# ── language variants ──────────────────────────────────────────────────
# A track may ship the same books in several meaning languages (HSK: vi + ko).
# Headwords, order and unit ids are shared (so card ids and progress survive a
# language switch); meanings, tips, translations, file tree and manifest differ.
# Pick one with `--lang <code>` or KIT_LANG; without `variants` nothing changes.
VARIANTS = CONFIG.get("variants") or {}


def _pick_variant():
    if not VARIANTS:
        return None
    lang = os.environ.get("KIT_LANG")
    if "--lang" in sys.argv:
        i = sys.argv.index("--lang")
        lang = sys.argv[i + 1]
        del sys.argv[i:i + 2]
    lang = lang or CONFIG.get("default_variant") or next(iter(VARIANTS))
    if lang not in VARIANTS:
        sys.exit(f"unknown --lang '{lang}' (variants: {', '.join(VARIANTS)})")
    return lang


VARIANT = _pick_variant()
_V = VARIANTS.get(VARIANT, {})
LANGUAGE = CONFIG["language"] | _V.get("language", {})
CONTENT_DIR = ROOT / _V.get("content_dir", "content/voca")
MANIFEST_PATH = ROOT / _V.get("manifest", "manifest.json")
UNIT_PROMPT = _V.get("unit_prompt", "unit.md")
LANG_ARGS = ["--lang", VARIANT] if VARIANT else []


def variant_content_dirs():
    """Every variant's content dir (just CONTENT_DIR for single-language tracks)."""
    if not VARIANTS:
        return {None: CONTENT_DIR}
    return {k: ROOT / v.get("content_dir", "content/voca") for k, v in VARIANTS.items()}
WORDS_PER_UNIT = CONFIG.get("words_per_unit", 100)
CHAPTER_SIZE = 10

BANDS = CONFIG["bands"]
BAND_BY_ID = {b["id"]: b for b in BANDS}

# ── scripts ────────────────────────────────────────────────────────────
HANGUL = re.compile(r"[가-힣]")
KANA = re.compile(r"[぀-ヿ]")
HAN = re.compile(r"[㐀-䶿一-鿿々〆]")
LATIN = re.compile(r"[A-Za-z]")

READING_RULES = {
    "ipa": (re.compile(r"^/[^/]+/$"), "IPA between slashes, e.g. /ˈmɒmənt/"),
    "kana": (re.compile(r"^[぀-ヿー・\s]+$"), "hiragana/katakana only, e.g. たべる"),
    # capitals for proper nouns (Ānlǐhuì), em dash for two-part sayings (歇后语)
    "pinyin": (re.compile(r"^[A-Za-züÜāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ' \-—]+$"), "pinyin with tone marks, e.g. xuéxí"),
    "romanization": (re.compile(r"^[A-Za-z' \-]+$"), "Revised Romanization, e.g. hakgyo"),
}

SCRIPT_OF = {"en": LATIN, "vi": LATIN, "ko": HANGUL, "ja": re.compile(r"[぀-ヿ㐀-鿿々]"), "zh": HAN}


def band_short(band_id: str) -> str:
    """score-000-326 → 000-326, jlpt-n5 → n5 (used in unit ids)."""
    return band_id.split("-", 1)[1] if band_id.startswith("score-") else band_id.split("-")[-1]


def unit_id(band_id: str, unit: int) -> str:
    return f"voca-{band_short(band_id)}-u{unit:03d}"


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).strip()
    return re.sub(r"\s+", " ", text)


def word_key(word: str, reading: str = "") -> str:
    """Duplicate key. Latin headwords compare case-insensitively; CJK
    homographs with different readings (上手 じょうず / うわて) stay distinct
    when the track keys on readings."""
    w = norm(word)
    if LATIN.search(w) and not (HAN.search(w) or KANA.search(w) or HANGUL.search(w)):
        w = w.lower()
    if LANGUAGE.get("dedupe_with_reading") and reading:
        # spacing and apostrophes in a reading never make a different word (kāi chē = kāichē)
        return f"{w}|{re.sub(r"[\s'’\-—]", "", norm(reading)).lower()}"
    return w


def parse_frontmatter(text: str):
    if not text.startswith("---\n") or "\n---\n" not in text:
        return None, text
    end = text.index("\n---\n")
    fields = {}
    for line in text[4:end].splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fields[k.strip()] = v.strip()
    return fields, text[end + 5:]


def word_lines(body: str):
    for lineno, line in enumerate(body.splitlines(), 1):
        s = line.strip()
        if s.startswith("- "):
            yield lineno, [p.strip() for p in s[2:].split("|")]


def unit_files():
    return sorted(CONTENT_DIR.rglob("unit-*.md"))


def curriculum():
    path = PLAN_DIR / "curriculum.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def plan_unit_path(band_id: str, unit: int) -> Path:
    return PLAN_DIR / "units" / band_id / f"unit-{unit:03d}.txt"


def read_plan_unit(band_id: str, unit: int):
    """→ (theme, [(word, reading)]) or None when the unit isn't planned yet."""
    path = plan_unit_path(band_id, unit)
    if not path.exists():
        return None
    theme, words = "", []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# theme:"):
            theme = line.split(":", 1)[1].strip()
        elif line.strip() and not line.startswith("#"):
            word, _, reading = line.partition("|")
            words.append((norm(word), norm(reading)))
    return theme, words
