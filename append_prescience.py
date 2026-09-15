#!/usr/bin/env python3
"""Append prescience scores to cache/prescience_scores.json and regenerate
04-prescience.md (ranked by final prescience score).

Usage: python3 append_prescience.py '<json blob array>'

Per-story blob fields:
  id                       (must exist in cache/scores.json; metadata reused)
  tier_hits                list of checklist IDs from prescience_scoring_guide.txt
                           Tier A (A1-A8, 5 pts), Tier B (B1-B12, 3 pts),
                           Tier C (C1-C10, 1 pt)
  precision                {"training": bool, "containment": bool,
                            "institutional": bool}   -> +2/+2/+1, max +5
  anti_patterns            list of codes (singular_ai, embodiment,
                           overnight_takeoff, freedom_personhood,
                           turing_threshold, never_wrong, perfect_memory,
                           single_controller, philosophical_debate,
                           loop_illusion, long_con, no_economics) -> -2 each
  justification            2 sentences: most prescient element + largest miss.

final = max(0, raw_hits + precision_bonus - 2*len(anti_patterns)) * era_multiplier
Era multipliers (guide section 9.4): pre-2010 x2.0; 2010-2014 x1.7;
2015-2018 x1.4; 2019-2021 x1.15; 2022+ x1.0.
"""
import json
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
PRES_JSON = os.path.join(BASE, "cache", "prescience_scores.json")
PRES_MD = os.path.join(BASE, "04-prescience.md")
SCORES_JSON = os.path.join(BASE, "cache", "scores.json")

A_IDS = {f"A{i}" for i in range(1, 9)}
B_IDS = {f"B{i}" for i in range(1, 13)}
C_IDS = {f"C{i}" for i in range(1, 11)}
ANTI_CODES = {"singular_ai", "embodiment", "overnight_takeoff",
              "freedom_personhood", "turing_threshold", "never_wrong",
              "perfect_memory", "single_controller", "philosophical_debate",
              "loop_illusion", "long_con", "no_economics"}
TIER_LABEL = {
    "A": "A (parallel instances, emergent culture, expendability, goal contagion, evaluator deception, sycophancy harm, inference-time capability, lab-internal incident)",
    "B": "B (reward hacking, mundane containment failure, autonomous cyber, social jailbreak, speed detection, hallucination-as-limit, state kill-switch, energy/land-use politics, cheap challenger, AI-on-AI research, human-misuse-first, transacting agents)",
    "C": "C (chat interface, codegen, synthetic media, sci discovery, white-collar, military w/ override, reactive regulation, firm concentration, US-China, personal-context surveillance)",
}
ANTI_LABEL = {
    "singular_ai": "singular AI", "embodiment": "embodiment default",
    "overnight_takeoff": "overnight takeoff", "freedom_personhood": "freedom/personhood seeking",
    "turing_threshold": "Turing-test threshold", "never_wrong": "AI never wrong",
    "perfect_memory": "perfect memory", "single_controller": "single controller",
    "philosophical_debate": "philosophical public debate", "loop_illusion": "clear in/out of loop",
    "long_con": "long-con hidden capabilities", "no_economics": "no economics",
}


def multiplier(year):
    year = int(year)
    if year < 2010:
        return 2.0
    if year <= 2014:
        return 1.7
    if year <= 2018:
        return 1.4
    if year <= 2021:
        return 1.15
    return 1.0


def hit_weight(h):
    if h in A_IDS:
        return 5
    if h in B_IDS:
        return 3
    if h in C_IDS:
        return 1
    raise ValueError(f"unknown tier hit {h!r}")


def compute(blob, meta):
    raw = sum(hit_weight(h) for h in blob["tier_hits"])
    prec = blob.get("precision", {})
    bonus = 2 * bool(prec.get("training")) + 2 * bool(prec.get("containment")) + 1 * bool(prec.get("institutional"))
    if bonus > 5:
        bonus = 5
    for code in blob["anti_patterns"]:
        if code not in ANTI_CODES:
            raise ValueError(f"unknown anti-pattern {code!r}")
    pen = 2 * len(blob["anti_patterns"])
    adjusted = max(0, raw + bonus - pen)
    mult = multiplier(meta["year"])
    blob["raw_hits"] = raw
    blob["precision_bonus"] = bonus
    blob["penalty"] = pen
    blob["adjusted"] = adjusted
    blob["multiplier"] = mult
    blob["final"] = round(adjusted * mult, 2)


def regenerate(records):
    records = sorted(records, key=lambda r: (-r["final"], int(r["year"])))
    with open(PRES_MD, "w") as f:
        f.write("# Stage 3b — Prescience ranking (vs. AI 2022-2026)\n\n")
        f.write("Scored per `prescience_scoring_guide.txt` §9-§10: Tier A hits ×5, Tier B ×3, Tier C ×1, ")
        f.write("precision bonus +0..5, anti-patterns −2 each (floor 0), then era multiplier ")
        f.write("(pre-2010 ×2.0 / 2010-14 ×1.7 / 2015-18 ×1.4 / 2019-21 ×1.15 / 2022+ ×1.0). ")
        f.write("Stories after Nov 2022 are reportage, not prediction. Oldest-first pass in progress; ")
        f.write("this file regenerates from cache/prescience_scores.json on every append.\n\n")
        f.write("| rank | Title | Author | Year | tier hits | raw | prec | pen | adj | ×mult | **final** | most prescient / largest miss |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for n, r in enumerate(records, 1):
            hits = " ".join(sorted(r["tier_hits"], key=lambda h: (h[0], int(h[1:])))) or "—"
            f.write(f"| {n} | [{r['title']}]({r['url']}) | {r['author']} | {r['year']} | {hits} | "
                    f"{r['raw_hits']} | +{r['precision_bonus']} | −{r['penalty']} | {r['adjusted']} | "
                    f"×{r['multiplier']} | **{r['final']}** | {r['justification']} |\n")


def main():
    blobs = json.loads(sys.argv[1])
    if not isinstance(blobs, list):
        blobs = [blobs]
    metas = {s["id"]: s for s in json.load(open(SCORES_JSON))}
    records = json.load(open(PRES_JSON)) if os.path.exists(PRES_JSON) else []
    existing = {r["id"] for r in records}

    for blob in blobs:
        if blob["id"] not in metas:
            print(f"ERROR: {blob['id']} not in scores.json — read it via batches only after Stage 3 scoring", file=sys.stderr)
            sys.exit(1)
        if blob["id"] in existing:
            print(f"SKIP: {blob['id']} already prescience-scored", file=sys.stderr)
            continue
        meta = metas[blob["id"]]
        for k in ("title", "author", "year", "karma", "url"):
            blob.setdefault(k, meta[k])
        compute(blob, meta)
        records.append(blob)
        existing.add(blob["id"])
        print(f"OK: prescience-scored {blob['title']} ({blob['year']}) → {blob['final']}")

    json.dump(records, open(PRES_JSON, "w"), indent=2)
    regenerate(records)
    print(f"wrote {PRES_MD} ({len(records)} stories)")


if __name__ == "__main__":
    main()
