#!/usr/bin/env python3
"""Validate every unit file against the app's parser and the track's spec.

Errors (must be 0 before publishing):
- frontmatter fields the app requires; band dir / id / score range agree
- exactly 6 fields per word line, none of word/meaning/reading/example/translation empty
- 100 words per unit (dummy units are exempt), multiple of 10
- reading format for the track (IPA / kana / pinyin / romanization)
- headword, meaning and translation are written in the right script
- no duplicate headword anywhere in the track (across all bands)
- when plan/units/<band>/unit-NNN.txt exists, the file holds exactly those words
- per-language tracks: the same book in every language lists the same headwords in the same order

Warnings: long tips, examples that don't show the headword, short examples.

Usage: python3 tools/validate_content.py [--lang <code>] [--quiet] [--unit <band>/<NNN>]
"""

import re
import sys

from kit import (BAND_BY_ID, CONTENT_DIR, LANGUAGE, READING_RULES, ROOT, SCRIPT_OF, VARIANT,
                 WORDS_PER_UNIT, norm, parse_frontmatter, read_plan_unit, unit_files, unit_id,
                 variant_content_dirs, word_key, word_lines)

REQUIRED_FM = ["id", "type", "level", "difficulty", "tags", "source", "version", "updated_at",
               "score_band_id", "score_min", "score_max"]
LANG = LANGUAGE
READING = LANG["reading"]
TIP_MAX = LANG.get("tip_max_chars", 45)


def stem_present(word: str, reading: str, example: str) -> bool:
    w = norm(word)
    ex = norm(example)
    lang = LANG["word"]
    if lang == "en":
        first = re.split(r"[\s/]", w.lower())[0]
        return first[: max(3, len(first) - 2)] in ex.lower()
    if lang == "ja":
        # conjugation eats okurigana: the kanji part (or the reading stem) must appear
        head = re.sub(r"[぀-ゟ]+$", "", w) or w
        return head in ex or (reading and reading[:-1] in ex)
    if lang == "ko":
        stem = w[:-1] if w.endswith("다") and len(w) > 1 else w
        return stem[: max(1, len(stem) - 1)] in ex
    return w in ex  # zh: no inflection


def headword_order(path):
    _, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return [word_key(p[0], p[2] if len(p) > 2 else "") for _, p in word_lines(body)]


def main() -> int:
    only = None
    if "--unit" in sys.argv:
        only = sys.argv[sys.argv.index("--unit") + 1]
    quiet = "--quiet" in sys.argv
    errors, warnings, notes = [], [], []
    seen: dict[str, str] = {}
    total = 0
    files = unit_files()
    if not files:
        print(f"No unit files under {CONTENT_DIR.relative_to(ROOT)}/")
        return 0

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        band_id = path.parent.name
        m = re.match(r"unit-(\d{3})\.md$", path.name)
        unit = int(m.group(1)) if m else 0
        tag = f"{band_id}/{unit:03d}"
        check = only is None or only == tag
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        offset = text[: len(text) - len(body)].count("\n")   # report file line numbers
        if fm is None:
            errors.append(f"{rel}: missing frontmatter"); continue
        dummy = fm.get("dummy") == "true"
        band = BAND_BY_ID.get(band_id)
        if band is None:
            errors.append(f"{rel}: unknown band directory '{band_id}'"); continue
        if check:
            for key in REQUIRED_FM:
                if not fm.get(key):
                    errors.append(f"{rel}: missing frontmatter '{key}'")
            if fm.get("score_band_id") != band_id:
                errors.append(f"{rel}: score_band_id != directory {band_id}")
            if fm.get("score_min") != str(band["min_score"]) or fm.get("score_max") != str(band["max_score"]):
                errors.append(f"{rel}: score_min/max must be {band['min_score']}/{band['max_score']}")
            if fm.get("id") != unit_id(band_id, unit):
                errors.append(f"{rel}: id must be {unit_id(band_id, unit)}")
            if fm.get("level") != str(band["order"]):
                errors.append(f"{rel}: level must be {band['order']}")

        plan = read_plan_unit(band_id, unit)
        planned = {word_key(w, r) for w, r in plan[1]} if plan else None
        got = set()
        count = 0
        for lineno, parts in word_lines(body):
            lineno += offset
            count += 1
            if len(parts) != 6:
                if check: errors.append(f"{rel}:{lineno}: expected 6 fields, got {len(parts)}")
                continue
            word, meaning, reading, tip, example, translation = parts
            key = word_key(word, reading)
            got.add(key)
            if key in seen and seen[key] != tag:
                errors.append(f"{rel}:{lineno}: duplicate '{word}' (also {seen[key]})")
            seen.setdefault(key, tag)
            if not check:
                continue
            for name, value in [("word", word), ("meaning", meaning), ("reading", reading),
                                ("example", example), ("translation", translation)]:
                if not value:
                    errors.append(f"{rel}:{lineno}: empty {name}")
            if reading and not READING_RULES[READING][0].match(reading):
                errors.append(f"{rel}:{lineno}: '{word}' reading '{reading}' — {READING_RULES[READING][1]}")
            for name, value, lang in [("word", word, LANG["word"]), ("meaning", meaning, LANG["meaning"]),
                                      ("example", example, LANG["word"]), ("translation", translation, LANG["meaning"]),
                                      ("tip", tip, LANG["tip"])]:
                if value and not SCRIPT_OF[lang].search(value):
                    errors.append(f"{rel}:{lineno}: {name} of '{word}' is not written in {lang}")
            if not tip:
                warnings.append(f"{rel}:{lineno}: '{word}' has no tip")
            elif len(tip) > TIP_MAX:
                warnings.append(f"{rel}:{lineno}: tip for '{word}' is {len(tip)} chars (> {TIP_MAX})")
            if example and not stem_present(word, reading, example):
                warnings.append(f"{rel}:{lineno}: example for '{word}' doesn't show the headword")
        total += count
        if not check:
            continue
        for lang, base in variant_content_dirs().items():
            sibling = base / band_id / path.name
            if lang != VARIANT and sibling.exists() and headword_order(sibling) != headword_order(path):
                errors.append(f"{rel}: headwords differ from the {lang} edition "
                              f"({sibling.relative_to(ROOT).as_posix()}) — same words, same order")
        if dummy:
            notes.append(f"{rel}: dummy unit ({count} words) — replace before launch")
            if count % 10:
                errors.append(f"{rel}: {count} words is not a multiple of 10")
            continue
        if count != WORDS_PER_UNIT:
            errors.append(f"{rel}: {count} words (must be {WORDS_PER_UNIT})")
        if planned is not None and got != planned:
            missing = len(planned - got); extra = len(got - planned)
            errors.append(f"{rel}: words differ from plan (missing {missing}, unplanned {extra})")

    if not quiet:
        for n in notes: print(f"NOTE  {n}")
        for w in warnings: print(f"WARN  {w}")
    for e in errors: print(f"ERROR {e}")
    print(f"\n{len(files)} files, {total} words · {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
