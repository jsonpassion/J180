#!/usr/bin/env python3
"""Plan the overnight word build so parallel writers never collide.

  python3 tools/plan.py status           where every band/unit stands
  python3 tools/plan.py wordlist-briefs  stage 1 prompts → plan/briefs/wordlist-<band>.md
  python3 tools/plan.py merge            plan/wordlists/<band>.md → plan/units/<band>/unit-NNN.txt
                                         (global de-dupe, 100 each, written units stay frozen)
  python3 tools/plan.py briefs           stage 2 prompts → plan/briefs/<band>/unit-NNN.md
  python3 tools/plan.py todo             units whose content file is missing or failing
  python3 tools/plan.py clear-dummy      delete dummy seed units before the real build
"""

import json
import re
import subprocess
import sys
from datetime import date

from kit import (BANDS, CONFIG, CONTENT_DIR, PLAN_DIR, ROOT, WORDS_PER_UNIT, curriculum, norm,
                 parse_frontmatter, plan_unit_path, read_plan_unit, unit_id, word_key)

PROMPTS = ROOT / "prompts"
CANDIDATE_SLACK = 1.2   # stage 1 asks for 20% more than it keeps


def content_path(band_id, unit):
    return CONTENT_DIR / band_id / f"unit-{unit:03d}.md"


def is_dummy(path):
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return bool(fm) and fm.get("dummy") == "true"


def themes(band_id):
    return curriculum().get(band_id, [])


def render(template, values):
    out = template
    for k, v in values.items():
        out = out.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if left:
        sys.exit(f"unfilled placeholders: {sorted(set(left))}")
    return out


def band_values(band):
    return {
        "EXAM": CONFIG["exam"]["mark"], "EXAM_KO": CONFIG["exam"]["name_ko"],
        "BAND_ID": band["id"], "BAND_LABEL": band["label"], "BAND_NAME": band["name"],
        "BAND_BRIEF": band["brief"], "LEVEL": band["order"], "DIFFICULTY": band["difficulty"],
        "SCORE_MIN": band["min_score"], "SCORE_MAX": band["max_score"],
        "SOURCE": CONFIG["source"], "TAGS": ", ".join(CONFIG["tags"]),
        "DATE": date.today().isoformat(), "UNITS": band["units"],
    }


def cmd_wordlist_briefs():
    template = (PROMPTS / "wordlist.md").read_text(encoding="utf-8")
    out_dir = PLAN_DIR / "briefs"; out_dir.mkdir(parents=True, exist_ok=True)
    per_unit = int(WORDS_PER_UNIT * CANDIDATE_SLACK)
    for band in BANDS:
        rows = themes(band["id"])
        if len(rows) < band["units"]:
            sys.exit(f"plan/curriculum.json has {len(rows)} themes for {band['id']}, needs {band['units']}")
        theme_lines = "\n".join(f"## unit-{i:03d} — {t}" for i, t in enumerate(rows[: band["units"]], 1))
        others = "\n".join(f"- {b['id']} ({b['label']}, {b['name']}): {b['brief']}" for b in BANDS)
        values = band_values(band) | {"THEMES": theme_lines, "PER_UNIT": per_unit, "ALL_BANDS": others,
                                       "TARGET_PATH": f"plan/wordlists/{band['id']}.md"}
        path = out_dir / f"wordlist-{band['id']}.md"
        path.write_text(render(template, values), encoding="utf-8")
        print("wrote", path.relative_to(ROOT))


def parse_wordlist(band_id):
    path = PLAN_DIR / "wordlists" / f"{band_id}.md"
    units, current = {}, None
    if not path.exists():
        return units
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^##\s*unit-(\d{3})", line)
        if m:
            current = int(m.group(1)); units.setdefault(current, []); continue
        s = line.strip().lstrip("-").strip()
        if current is None or not s or s.startswith("#"):
            continue
        s = re.sub(r"^\d+[.)]\s*", "", s)
        word, _, reading = s.partition("|")
        if norm(word):
            units[current].append((norm(word), norm(reading)))
    return units


def cmd_merge():
    taken = {}
    report = []
    for band in BANDS:
        candidates = parse_wordlist(band["id"])
        for unit in range(1, band["units"] + 1):
            tag = f"{band['id']}/{unit:03d}"
            existing = read_plan_unit(band["id"], unit)
            written = content_path(band["id"], unit)
            if existing and written.exists() and not is_dummy(written):
                for w, r in existing[1]:           # frozen: its words are in the book already
                    taken.setdefault(word_key(w, r), tag)
                report.append((tag, len(existing[1]), "frozen"))
                continue
            picked = []
            for w, r in candidates.get(unit, []):
                key = word_key(w, r)
                if key in taken:
                    continue
                taken[key] = tag
                picked.append((w, r))
                if len(picked) == WORDS_PER_UNIT:
                    break
            if not picked:
                report.append((tag, 0, "no candidates")); continue
            theme = (themes(band["id"]) + [""] * unit)[unit - 1]
            path = plan_unit_path(band["id"], unit); path.parent.mkdir(parents=True, exist_ok=True)
            body = "\n".join(f"{w} | {r}" if r else w for w, r in picked)
            path.write_text(f"# theme: {theme}\n# unit: {unit_id(band['id'], unit)}\n{body}\n", encoding="utf-8")
            report.append((tag, len(picked), "ok" if len(picked) == WORDS_PER_UNIT else "SHORT"))
    short = [r for r in report if r[2] in ("SHORT", "no candidates")]
    for tag, n, state in report:
        if state != "ok":
            print(f"{state:>13}  {tag}  {n}/{WORDS_PER_UNIT}")
    print(f"\n{len(report)} units planned, {len(short)} short. "
          + ("Top up the short units in plan/wordlists and run merge again." if short else "Ready for `plan.py briefs`."))
    return 1 if short else 0


def cmd_briefs():
    template = (PROMPTS / "unit.md").read_text(encoding="utf-8")
    n = 0
    for band in BANDS:
        for unit in range(1, band["units"] + 1):
            plan = read_plan_unit(band["id"], unit)
            if not plan or len(plan[1]) != WORDS_PER_UNIT:
                continue
            theme, words = plan
            headwords = "\n".join(f"{i}. {w}" + (f" | {r}" if r else "") for i, (w, r) in enumerate(words, 1))
            values = band_values(band) | {
                "UNIT": f"{unit:03d}", "UNIT_ID": unit_id(band["id"], unit), "THEME": theme,
                "HEADWORDS": headwords, "TARGET_PATH": f"content/voca/{band['id']}/unit-{unit:03d}.md",
            }
            path = PLAN_DIR / "briefs" / band["id"] / f"unit-{unit:03d}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(render(template, values), encoding="utf-8"); n += 1
    print(f"wrote {n} unit briefs under plan/briefs/")


def failing_units():
    out = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_content.py"), "--quiet"],
                         capture_output=True, text=True).stdout
    return {m.group(1) + "/" + m.group(2) for m in re.finditer(r"content/voca/([^/]+)/unit-(\d{3})\.md", out)}


def cmd_todo():
    failing = failing_units()
    todo = []
    for band in BANDS:
        for unit in range(1, band["units"] + 1):
            tag = f"{band['id']}/{unit:03d}"
            path = content_path(band["id"], unit)
            if not path.exists() or is_dummy(path) or tag in failing:
                todo.append(f"plan/briefs/{tag.replace('/', '/unit-')}.md")
    print("\n".join(todo) if todo else "nothing to do — every planned unit is written and valid")
    return 0


def cmd_status():
    for band in BANDS:
        cands = sum(len(v) for v in parse_wordlist(band["id"]).values())
        planned = sum(1 for u in range(1, band["units"] + 1) if read_plan_unit(band["id"], u))
        written = sum(1 for u in range(1, band["units"] + 1)
                      if content_path(band["id"], u).exists() and not is_dummy(content_path(band["id"], u)))
        print(f"{band['id']:<16} {band['label']:<10} candidates {cands:>5} · planned {planned:>3}/{band['units']} · written {written:>3}/{band['units']}")


def cmd_clear_dummy():
    removed = [p for p in CONTENT_DIR.rglob("unit-*.md") if is_dummy(p)]
    for p in removed:
        p.unlink()
    print(f"removed {len(removed)} dummy units")


if __name__ == "__main__":
    commands = {"status": cmd_status, "wordlist-briefs": cmd_wordlist_briefs, "merge": cmd_merge,
                "briefs": cmd_briefs, "todo": cmd_todo, "clear-dummy": cmd_clear_dummy}
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        sys.exit(__doc__)
    sys.exit(commands[sys.argv[1]]() or 0)
