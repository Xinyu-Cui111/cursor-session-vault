#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-time: move sessions/YYYY-MM-DD/*.md into sessions/{project}/{date}/ using frontmatter."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

VAULT = Path(__file__).resolve().parent
SESSIONS = VAULT / "sessions"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_frontmatter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    block = text[3:end].strip()
    data: dict = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        try:
            data[k] = json.loads(v)
        except json.JSONDecodeError:
            data[k] = v.strip('"')
    return data


def main() -> None:
    moved = 0
    skipped = 0
    for day_dir in sorted(SESSIONS.iterdir()):
        if not day_dir.is_dir() or not DATE_RE.match(day_dir.name):
            continue
        for md in day_dir.glob("*.md"):
            text = md.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            project = str(fm.get("project") or "unknown-project").strip() or "unknown-project"
            # sanitize like save-session safe_slug light
            project = re.sub(r'[\\/:*?"<>|]+', "_", project).strip("._-") or "unknown-project"
            dest_dir = SESSIONS / project / day_dir.name
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / md.name
            if dest.resolve() == md.resolve():
                skipped += 1
                continue
            if dest.exists():
                print(f"SKIP exists: {dest}")
                skipped += 1
                continue
            shutil.move(str(md), str(dest))
            print(f"MOVE {md.relative_to(SESSIONS)} -> {dest.relative_to(SESSIONS)}")
            moved += 1
        # remove empty date dir
        try:
            if day_dir.is_dir() and not any(day_dir.iterdir()):
                day_dir.rmdir()
                print(f"RMDIR {day_dir.name}")
        except OSError:
            pass
    print(f"done moved={moved} skipped={skipped}")


if __name__ == "__main__":
    main()
