#!/usr/bin/env python3
"""Apply Stage 2 DROP decisions for serial continuation chapters detected by
detect_serials.py, collapsing each serial to a single representative post.
Idempotent: append_filter.py already skips ids it's seen.
"""
import json
import os
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
groups = json.load(open(os.path.join(BASE, "cache", "serial_groups.json")))
digest = {e["_id"]: e for e in json.load(open(os.path.join(BASE, "cache", "digest.json")))}

# Three Worlds Collide: override representative from the (0/8) ToC stub to
# the actual first chapter.
OVERRIDE_REPRESENTATIVE = {
    "HawFh7RvDM4RyoJ2d": "n5TqCuizyJDfAPjkr",  # (0/8) stub -> Baby-Eating Aliens (1/8)
}

decisions = []
for g in groups:
    rep_id = g["representative_id"]
    rep_id = OVERRIDE_REPRESENTATIVE.get(rep_id, rep_id)
    rep_title = digest[rep_id]["title"]
    label = {
        ("chapter-series", "Eliezer Yudkowsky"): "HPMOR",
        ("prefix-series", "lsusr", "bayeswatch"): "Bayeswatch",
        ("prefix-series", "alkjash", "murphy’s quest ch"): "Murphy's Quest",
        ("nm-series", "Eliezer Yudkowsky", 8): "Three Worlds Collide",
        ("prefix-series", "Henry Prowbell", "harry potter and the methods of psychomagic | chapter"): "Harry Potter and the Methods of Psychomagic",
    }.get(tuple(g["key"]), g["key"][-1])

    for mid, mtitle in zip(g["member_ids"], g["member_titles"]):
        if mid == rep_id:
            continue
        reason = (f"serial continuation of '{label}' (represented in the candidate "
                  f"set by '{rep_title}', {rep_id}) — collapsed per the task's serial "
                  f"convention, since this tag turned out NOT to have been applied only "
                  f"to the first chapter for this work (see NOTES.md)")
        decisions.append({"id": mid, "title": mtitle, "decision": "DROP", "reason": reason})

    # (0/8) stub itself, if it was the original (now-overridden) representative
    if g["representative_id"] in OVERRIDE_REPRESENTATIVE:
        stub_id = g["representative_id"]
        stub_title = digest[stub_id]["title"]
        decisions.append({
            "id": stub_id, "title": stub_title, "decision": "DROP",
            "reason": f"table-of-contents/index stub for '{label}', not narrative content — represented by '{rep_title}' instead"
        })

print(f"{len(decisions)} serial-continuation drop decisions to append")
result = subprocess.run(
    ["python3", os.path.join(BASE, "append_filter.py"), json.dumps(decisions)],
    capture_output=True, text=True,
)
print(result.stdout[-2000:])
if result.returncode != 0:
    print("STDERR:", result.stderr)
