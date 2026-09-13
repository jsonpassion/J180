"""Shared helpers for the vocabulary content kit (config, files, scripts).

Every sister-app content repo carries the same tools; only
content.config.json, plan/curriculum.json and the prompt rules differ.
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = json.loads((ROOT / "content.config.json").read_text(encoding="utf-8"))
CONTENT_DIR = ROOT / "content" / "voca"
PLAN_DIR = ROOT / "plan"
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
    "pinyin": (re.compile(r"^[A-Za-züÜāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ' \-]+$"), "pinyin with tone marks, e.g. xuéxí"),
    "romanization": (re.compile(r"^[A-Za-z' \-]+$"), "Revised Romanization, e.g. hakgyo"),
}

SCRIPT_OF = {"en": LATIN, "ko": HANGUL, "ja": re.compile(r"[぀-ヿ㐀-鿿々]"), "zh": HAN}


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
    if CONFIG["language"].get("dedupe_with_reading") and reading:
        return f"{w}|{norm(reading)}"
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
