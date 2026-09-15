#!/usr/bin/env python3
"""Append one Stage 2 prefilter decision immediately (resumable, auditable).
Usage: python3 append_filter.py '<json blob>'
blob: {id, title, author, decision: KEEP|DROP|BORDERLINE, reason}
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
DECISIONS_PATH = os.path.join(BASE, "cache", "filter_decisions.jsonl")

VALID = {"KEEP", "DROP", "BORDERLINE"}


def already_decided():
    seen = set()
    if os.path.exists(DECISIONS_PATH):
        with open(DECISIONS_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                seen.add(json.loads(line)["id"])
    return seen


def main():
    parsed = json.loads(sys.argv[1])
    blobs = parsed if isinstance(parsed, list) else [parsed]
    seen = already_decided()
    with open(DECISIONS_PATH, "a") as f:
        for blob in blobs:
            if blob["decision"] not in VALID:
                raise ValueError(f"decision must be one of {VALID}, got {blob['decision']!r}")
            if blob["id"] in seen:
                print(f"SKIP: {blob['id']} already decided", file=sys.stderr)
                continue
            f.write(json.dumps(blob) + "\n")
            seen.add(blob["id"])
            print(f"OK: {blob['decision']} — {blob['title']}")


if __name__ == "__main__":
    main()
