#!/usr/bin/env python3
"""Generate manifest.json from content/voca/<band>/unit-NNN.md
(per-language tracks: manifest.<lang>.json from content/<lang>/voca, pick with --lang).

SHA-256 per file (the app re-downloads on change) and a content-hash version,
so the manifest changes exactly when a word file does.

Usage: python3 tools/build_manifest.py [--lang <code>] [--check]
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timezone

from kit import BANDS, CONFIG, MANIFEST_PATH, ROOT, VARIANT, parse_frontmatter, unit_files


def entries():
    out = []
    for path in unit_files():
        raw = path.read_bytes()
        fm, _ = parse_frontmatter(raw.decode("utf-8"))
        m = re.search(r"unit-(\d+)\.md$", path.name)
        out.append({
            "id": fm["id"], "type": fm["type"], "level": int(fm["level"]),
            "path": path.relative_to(ROOT).as_posix(),
            "checksum_sha256": hashlib.sha256(raw).hexdigest(),
            "updated_at": fm["updated_at"],
            "score_band_id": fm.get("score_band_id"),
            "score_min": int(fm["score_min"]) if fm.get("score_min") else None,
            "score_max": int(fm["score_max"]) if fm.get("score_max") else None,
            "unit_title": fm.get("unit_title"), "unit_title_ko": fm.get("unit_title_ko"),
            "unit_symbol": fm.get("unit_symbol"),
            "sequence": int(m.group(1)) if m else 0,
        })
    return out


def build():
    items = entries()
    version = "c-" + hashlib.sha256("".join(e["checksum_sha256"] for e in items).encode()).hexdigest()[:12]
    bands = [{"id": b["id"], "label": b["label"], "min_score": b["min_score"], "max_score": b["max_score"],
              "order": b["order"]} for b in BANDS]
    return {
        "version": version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": 1,
        "track": CONFIG["track"],
        **({"language": VARIANT} if VARIANT else {}),
        "profile": {"target_score": CONFIG["target_score"], "daily_study_minutes": 5,
                    "voca_review_rule": "hoedok-rounds", "free_chapters": CONFIG.get("free_chapters", 10)},
        "score_band_policy": {"version": "3.0", "rule": CONFIG.get("band_rule", "four-tier"), "bands": bands},
        "entries": items,
    }


def main() -> int:
    manifest = build()
    if "--check" in sys.argv:
        current = json.loads(MANIFEST_PATH.read_text()) if MANIFEST_PATH.exists() else {}
        ok = current.get("version") == manifest["version"]
        name = MANIFEST_PATH.name
        print(f"{name} is up to date" if ok else f"{name} is stale — run tools/build_manifest.py")
        return 0 if ok else 1
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote {MANIFEST_PATH.name} — version {manifest['version']}, {len(manifest['entries'])} entries")
    return 0


if __name__ == "__main__":
    sys.exit(main())
