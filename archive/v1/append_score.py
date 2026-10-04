#!/usr/bin/env python3
"""Append one story's score to 03-scores.md and cache/scores.json immediately.
Usage: python3 append_score.py '<json blob>'

json blob fields required:
  id, title, author, year, karma, url, wordCount,
  posthuman, rigor, idea_density, craft, form, brevity  (0-5 ints)
  nearest_neighbor  (Egan / Vinge / Stross / Terrarium / none)
  note  (short internal justification, 1 sentence, not the public blurb)
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SCORES_JSON = os.path.join(BASE, "cache", "scores.json")
SCORES_MD = os.path.join(BASE, "03-scores.md")

DIMENSIONS = ["posthuman", "rigor", "idea_density", "craft", "form", "brevity"]


def weighted_total(s):
    return round(1.5 * s["posthuman"] + 1.5 * s["rigor"] + s["idea_density"] + s["craft"] + s["form"] + s["brevity"], 2)


def ensure_header():
    if not os.path.exists(SCORES_MD):
        with open(SCORES_MD, "w") as f:
            f.write("# Stage 3 — Scores\n\n")
            f.write("Appended one row at a time as each story is read and scored in full. "
                    "Weighted total = 1.5×posthuman + 1.5×rigor + idea_density + craft + form + brevity (max 27).\n\n")
            f.write("| # | Title | Author | Year | Karma | posthuman | rigor | idea_density | craft | form | brevity | weighted | nearest_neighbor | note |\n")
            f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")


def main():
    parsed = json.loads(sys.argv[1])
    blobs = parsed if isinstance(parsed, list) else [parsed]

    scores = []
    if os.path.exists(SCORES_JSON):
        with open(SCORES_JSON) as f:
            scores = json.load(f)
    existing_ids = {s["id"] for s in scores}
    ensure_header()

    for blob in blobs:
        for d in DIMENSIONS:
            v = blob[d]
            if not isinstance(v, int) or not (0 <= v <= 5):
                raise ValueError(f"{d} must be an int 0-5, got {v!r}")
        if blob["id"] in existing_ids:
            print(f"SKIP: {blob['id']} already scored", file=sys.stderr)
            continue

        blob["weighted_total"] = weighted_total(blob)
        scores.append(blob)
        existing_ids.add(blob["id"])
        with open(SCORES_JSON, "w") as f:
            json.dump(scores, f, indent=2)

        n = len(scores)
        row = (
            f"| {n} | [{blob['title']}]({blob['url']}) | {blob['author']} | {blob['year']} | {blob['karma']} | "
            f"{blob['posthuman']} | {blob['rigor']} | {blob['idea_density']} | {blob['craft']} | {blob['form']} | {blob['brevity']} | "
            f"{blob['weighted_total']} | {blob['nearest_neighbor']} | {blob.get('note', '')} |"
        )
        with open(SCORES_MD, "a") as f:
            f.write(row + "\n")
        print(f"OK: appended #{n} {blob['title']} (weighted {blob['weighted_total']})")


if __name__ == "__main__":
    main()
