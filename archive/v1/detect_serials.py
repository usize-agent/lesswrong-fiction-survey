#!/usr/bin/env python3
"""Detect serialized works whose chapters were each individually Fiction-tagged
(breaking the assumed 'tag only the first post' convention). Groups them so
Stage 2 can collapse each serial down to one representative entry instead of
scoring every chapter separately.
"""
import json
import os
import re
from collections import defaultdict

BASE = os.path.dirname(os.path.abspath(__file__))
digest = json.load(open(os.path.join(BASE, "cache", "digest.json")))
by_id = {e["_id"]: e for e in digest}

groups = defaultdict(list)

CHAPTER_RE = re.compile(r"^chapter\s+(\d+)\b", re.IGNORECASE)
NM_RE = re.compile(r"\((\d+)\s*/\s*(\d+)\)")
NUMBERED_PREFIX_RE = re.compile(r"^(.*?\D)\s*(\d+(?:\.\d+)?)\s*[:\-]")

for e in digest:
    title = e["title"]
    author = e["author"]

    m = CHAPTER_RE.match(title)
    if m:
        groups[("chapter-series", author)].append((int(m.group(1)), e))
        continue

    m = NM_RE.search(title)
    if m:
        n, total = int(m.group(1)), int(m.group(2))
        groups[("nm-series", author, total)].append((n, e))
        continue

    m = NUMBERED_PREFIX_RE.match(title)
    if m:
        prefix = m.group(1).strip()
        if len(prefix) >= 4:
            groups[("prefix-series", author, prefix.lower())].append((float(m.group(2)), e))
        continue

serials = {k: v for k, v in groups.items() if len(v) >= 3}

print(f"{len(serials)} candidate serial groups (size >= 3):\n")
summary = []
for key, members in sorted(serials.items(), key=lambda kv: -len(kv[1])):
    members.sort(key=lambda t: t[0])
    first = members[0][1]
    total_words = sum(e["wordCount"] for _, e in members)
    print(f"{key} -> {len(members)} parts, first='{first['title']}' ({first['_id']}), total words={total_words}")
    summary.append({
        "key": list(key),
        "representative_id": first["_id"],
        "representative_title": first["title"],
        "member_ids": [e["_id"] for _, e in members],
        "member_titles": [e["title"] for _, e in members],
    })

with open(os.path.join(BASE, "cache", "serial_groups.json"), "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nWrote cache/serial_groups.json")
