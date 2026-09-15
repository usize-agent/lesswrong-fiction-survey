#!/usr/bin/env python3
"""Regenerate 02-filtered.md from cache/filter_decisions.jsonl. Safe to re-run
any time during the Stage 2 pass to check progress / audit so far.
"""
import json
import os
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
DECISIONS_PATH = os.path.join(BASE, "cache", "filter_decisions.jsonl")
DIGEST_PATH = os.path.join(BASE, "cache", "digest.json")


def main():
    decisions = []
    with open(DECISIONS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                decisions.append(json.loads(line))

    digest = {d["_id"]: d for d in json.load(open(DIGEST_PATH))}

    counts = Counter(d["decision"] for d in decisions)
    total = len(decisions)

    lines = []
    lines.append("# Stage 2 — Cheap prefilter\n")
    lines.append(f"{total} candidates classified.\n")
    lines.append("| Decision | Count |")
    lines.append("|---|---|")
    for k in ["KEEP", "BORDERLINE", "DROP"]:
        lines.append(f"| {k} | {counts.get(k, 0)} |")
    lines.append("")

    lines.append("## Kept\n")
    lines.append("| Title | Author | Year | Reason |")
    lines.append("|---|---|---|---|")
    for d in decisions:
        if d["decision"] == "KEEP":
            meta = digest.get(d["id"], {})
            lines.append(f"| {d['title']} | {d.get('author', meta.get('author',''))} | {meta.get('year','')} | {d.get('reason','')} |")
    lines.append("")

    lines.append("## Borderline (flagged, not dropped — needs a human call)\n")
    lines.append("| Title | Author | Year | Reason |")
    lines.append("|---|---|---|---|")
    for d in decisions:
        if d["decision"] == "BORDERLINE":
            meta = digest.get(d["id"], {})
            lines.append(f"| {d['title']} | {d.get('author', meta.get('author',''))} | {meta.get('year','')} | {d.get('reason','')} |")
    lines.append("")

    lines.append("## Dropped\n")
    lines.append("| Title | Author | Year | Reason |")
    lines.append("|---|---|---|---|")
    for d in decisions:
        if d["decision"] == "DROP":
            meta = digest.get(d["id"], {})
            lines.append(f"| {d['title']} | {d.get('author', meta.get('author',''))} | {meta.get('year','')} | {d.get('reason','')} |")
    lines.append("")

    with open(os.path.join(BASE, "02-filtered.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote 02-filtered.md: {total} classified (KEEP={counts.get('KEEP',0)}, BORDERLINE={counts.get('BORDERLINE',0)}, DROP={counts.get('DROP',0)})")


if __name__ == "__main__":
    main()
