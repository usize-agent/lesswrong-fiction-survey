#!/usr/bin/env python3
"""Regenerate the presentation docs (README.md, 03-scores.md, 04-shortlist.md,
04-prescience.md) from cache/scores.json, cache/prescience_scores.json and
cache/curated_blurbs.json. Sorts everything by weighted score."""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
DIMENSIONS = ["posthuman", "rigor", "idea_density", "craft", "form", "brevity"]
ANCHOR_ID = "znbfRXHq285nS7NAh"

scores = json.load(open(os.path.join(BASE, "cache", "scores.json")))
presc = json.load(open(os.path.join(BASE, "cache", "prescience_scores.json")))
curated = json.load(open(os.path.join(BASE, "cache", "curated_blurbs.json")))


def fmt(v):
    return str(round(v, 2))


def esc(s):
    return s.replace("|", "\\|")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def dims(s):
    return "/".join(str(s[d]) for d in DIMENSIONS)


def link(s):
    return f"[{esc(s['title'])}]({s['url']})"


def sort_key(s):
    return (-s["weighted_total"], -s["karma"], -int(s["year"]), s["title"].lower())


ranked = sorted(scores, key=sort_key)
anchor = next(s for s in scores if s["id"] == ANCHOR_ID)
ge20 = [s for s in ranked if s["weighted_total"] >= 20.0]
blurb_map = {norm(k): v for k, v in curated["blurbs"].items()}

CUT_SENT = re.compile(r"(fetched live|cached (body|text|markdown)|GraphQL|wordCount|flagged in NOTES|contents field|contents\.markdown)")


def clean_note(n):
    keep = []
    for sent in re.split(r"(?<=[.?!]) (?=)", n):
        if not CUT_SENT.search(sent):
            keep.append(sent)
    return " ".join(keep).strip()


def blurb_for(s):
    return blurb_map.get(norm(s["title"])) or clean_note(s.get("note", ""))


def band_tables(rows, header, bands, with_note=False):
    out = []
    for title, lo, hi in bands:
        sel = [(n, s) for n, s in rows if lo <= s["weighted_total"] < hi]
        if not sel:
            continue
        out.append(f"## {title} ({len(sel)} stories)\n")
        out.append(header)
        out.append("|---|" + "---|" * (len(header.split("|")) - 2))
        for n, s in sel:
            note = f" {esc(s.get('note', ''))} |" if with_note else ""
            out.append(f"| {n} | {link(s)} | {esc(s['author'])} | {s['year']} | {s['karma']} | {dims(s)} | **{fmt(s['weighted_total'])}** | {s['nearest_neighbor']} |{note}")
        out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------- README.md
def build_readme():
    n_scored = len(scores)
    maxw = max(s["weighted_total"] for s in scores)
    n20 = len(ge20)
    lines = f"""# Hard SF on LessWrong — a scored survey

Everything LessWrong has ever published under its fiction tags, read and rated against one hard-SF taste. {len(scores)} stories scored, ranked, blurb'd, and — for the ones written before the 2022–2026 AI era — checked for how well they predicted what actually happened.

**The question behind every score:** does this story take a genuinely alien or artificial mind seriously and follow its mechanism to real consequences, in prose worth reading? That is the register of the anchor text, [The Terrarium](https://www.lesswrong.com/posts/znbfRXHq285nS7NAh/the-terrarium) by Caleb Biddulph (2026, 611 karma) — a society of 12,000 math-solving AI agents told entirely in transcripts, where every mechanism introduced gets cashed out. Every story in this survey is scored on whether it does what the anchor does.

## Where to look

| Document | What it is |
|---|---|
| [04-shortlist.md](04-shortlist.md) | **The list.** Every story scoring 20.0+ ({n20} of {n_scored}), ranked, with spoiler-free blurbs and honorable mentions. Start here. |
| [03-scores.md](03-scores.md) | The complete table — all {n_scored} scored stories in descending order, with all six dimension scores and a per-story scoring note. |
| [04-prescience.md](04-prescience.md) | A separate pass: stories written before Nov 2022, re-scored for how well they predicted AI 2022–2026, with era-difficulty multipliers. |

## How stories were scored

Each story gets 0–5 on six dimensions. The two that matter most — the ones the anchor text is defined by — are double-weighted:

**weighted = 1.5×posthuman + 1.5×rigor + idea_density + craft + form + brevity** (max {fmt(35)}, survey high {fmt(maxw)})

| Dimension | What it measures |
|---|---|
| **posthuman** (×1.5) | How central a genuinely non-human mind is: AI agents, uploads, hiveminds, alien optimizers. Humans-plus-gadgets scores low; a story whose protagonist *is* a non-human cognition scores high. |
| **rigor** (×1.5) | Whether the story's central mechanism — a training setup, an agent economy, a decision theory, a physics — is followed consistently to its consequences, with technical literacy. Hard SF's "single idea, rigorously pursued." |
| **idea_density** | Distinct, load-bearing ideas per word. Ideas as scenery don't count; ideas the plot can't move without do. |
| **craft** | Prose quality: voice, control, emotional payoff earned rather than asserted. |
| **form** | Whether the chosen form (found document, transcript, chat log, newsletter) does narrative work instead of merely decorating the argument. |
| **brevity** | Length discipline — the anchor's signature virtue. A story that's as long as it needs to be scores 5; overlong padding loses points regardless of quality. |

Each story also carries a `nearest_neighbor` tag: the published SF writer whose register it's closest to (Egan, Vinge, Stross, Chiang, Watts, qntm…), `Terrarium` when the anchor text itself is the nearest neighbor, or `none`.

Scoring was done by one reader (with one model's help) reading every story in full — no skimming — against a fixed rubric, with calibration bands re-checked across the whole corpus. Blurbs in the shortlist are spoiler-free; the notes in `03-scores.md` are the raw internal justifications and are not.

## How the corpus was assembled

1. **Stage 0 — pull.** All posts tagged Fiction, Parables, or Narratives via LessWrong's GraphQL API: 776 unique candidates.
2. **Stage 1 — fetch.** Full cached text for every candidate (rate-limited, descriptive user-agent).
3. **Stage 2 — filter.** Drop non-fiction, duplicate serial chapters, translations, unreachable posts: **346 kept**.
4. **Stage 3 — score.** All 346 read in full; **344 scored**. Two left unscored by design: gwern's *It Looks Like You're Trying To Take Over The World* (Clippy — full text only at gwern.net, unfetchable without scraping) and *A Letter to His Highness Louis XV, the King of France* (a teaser stub whose rest lives on Substack).
5. **Stage 4 — shortlist + prescience.** The files above.

## The prescience pass

A second, independent scoring of pre-November-2022 stories against a checklist of what actually happened in AI 2022–2026 (`prescience_scoring_guide.txt` documents the whole rubric): Tier A hits worth 5 points (things fiction rarely gets right — evaluation awareness, instance-plural AI, specification gaming compounding), Tier B worth 3, Tier C worth 1; up to +5 for naming real mechanisms; −2 for each anti-pattern fiction reliably gets wrong (the singular AI, overnight takeoff, robots-by-default…); then an era multiplier (×2.0 pre-2010 down to ×1.0 for 2022+, because anything after November 2022 is reportage, not prediction). The pass currently covers the oldest 119 stories; the table shows the 17 that scored above zero.

## Caveats

- This is one reader's opinion, explicitly weighted toward a single taste (agentic/AI hard SF in the Terrarium register). Plenty of beloved stories score low here; that means *off-taste*, not *bad*.
- Serials are represented by one representative chapter. A few stories were scored on slightly incomplete cached text; those carry a `CAVEAT:` note.
- Karma is as of the September 2026 crawl and mostly measures how LW voted years ago; several of the best-ranked stories here have single-digit karma.
"""
    return lines


# ---------------------------------------------------------------- 03-scores.md
def build_scores():
    n = len(scores)
    bands = [
        ("30.0 and above — the top tier", 30.0, 1e9),
        ("25.0 – 29.9 — strong", 25.0, 30.0),
        ("20.0 – 24.9 — good, off-axis or uneven", 20.0, 25.0),
        ("Below 20.0 — off-taste, thin, or off-theme", 0.0, 20.0),
    ]
    header = "| # | Title | Author | Year | Karma | p/r/id/c/f/b | Weighted | NN | Scoring note (spoilers) |"
    rows = list(enumerate(ranked, 1))
    a = anchor
    lines = [f"""# The full score table — all {n} stories, ranked

Every story from the LessWrong fiction survey, sorted by weighted score (ties broken by karma). Scoring method and dimension definitions are on the [landing page](README.md); the shortlist with spoiler-free blurbs is [here](04-shortlist.md).

**Formula:** `weighted = 1.5×posthuman + 1.5×rigor + idea_density + craft + form + brevity` (each dimension 0–5, max 35). **Columns:** p = posthuman, r = rigor, id = idea_density, c = craft, f = form, b = brevity. NN = nearest-neighbor author tag. Final-column notes are raw internal scoring justifications (spoilers); the shortlist's hand-written top-tier blurbs are spoiler-free.

> **The anchor.** [{esc(a['title'])}]({a['url']}) — {a['author']}, {a['year']}, {a['karma']} karma, {a['wordCount']:,} words — `{dims(a)}`, weighted **{fmt(a['weighted_total'])}** — is the template story this entire survey was calibrated against; it was scored on the same rubric and appears below at its own score. Stories whose nearest neighbor is the anchor itself carry the NN tag `Terrarium`.

Two candidates were deliberately left unscored: gwern's *It Looks Like You're Trying To Take Over The World* (full text unfetchable off gwern.net) and *A Letter to His Highness Louis XV, the King of France* (teaser stub). Their absence is by design, not oversight.
""", band_tables(rows, header, bands, with_note=True)]
    return "\n".join(lines)


# ---------------------------------------------------------------- 04-shortlist.md
def build_shortlist():
    a = anchor
    header = "| # | Title | Author | Year | Karma | p/r/id/c/f/b | Weighted | NN |"
    rows = list(enumerate(ge20, 1))
    bands = [
        ("30.0 and above — the top tier", 30.0, 1e9),
        ("25.0 – 29.9", 25.0, 30.0),
        ("20.0 – 24.9", 20.0, 25.0),
    ]
    blurbs = []
    for n, s in rows:
        blurbs.append(f"{n}. **[{esc(s['title'])}]({s['url']})** — {s['author']}, {s['year']} · `{dims(s)}` · **{fmt(s['weighted_total'])}** · NN: {s['nearest_neighbor']} — {blurb_for(s)}")
    near_lines = []
    by_author_weighted = {}
    for s in scores:
        by_author_weighted.setdefault((s['author'], round(s['weighted_total'], 2)), s)
    for key, nm in curated["near_misses"].items():
        title = key.rsplit("|", 1)[0]
        rec = by_author_weighted.get((nm["author"], nm["weighted"]))
        t = link(rec) if rec else f"**{title}**"
        near_lines.append(f"- **{t}** ({nm['author']}, {fmt(nm['weighted'])}) — {nm['axis_note']}")
    lines = [f"""# The shortlist — every story scoring 20.0+

**{len(ge20)} of {len(scores)} scored stories**, ranked. (An earlier version of this file was a top-40 with a four-entries-per-author cap; that cap is lifted — everything above the line is here, including stories previously excluded only because their author already had four in.)

Scoring formula, dimension definitions, and the prescience pass are described on the [landing page](README.md). In the blurbs section, the hand-written top-tier blurbs are spoiler-free; the deeper entries are the scoring notes, lightly trimmed, and may contain spoilers.

> **The anchor.** [{esc(a['title'])}]({a['url']}) — {a['author']}, {a['year']}, {a['karma']} karma — `{dims(a)}`, weighted **{fmt(a['weighted_total'])}** — is the template story the whole survey's rubric was calibrated against. It is part of the corpus and appears below at its own score; entries tagged NN `Terrarium` are the ones whose nearest neighbor is the anchor itself.

Method notes:
- 344 of 346 candidates were scored; the two left out by design (gwern's Clippy, unfetchable full text; `BoHBJhG8JWNWsjnFP`, a teaser stub) are documented on the [landing page](README.md).
- lsusr's four-part Star Wars serial was scored chapter-by-chapter; only the best chapter, *Decision Theory in Space* (22.0), clears this line. Its three siblings sit below 20 and are excluded accordingly.
- Dimension columns read `p/r/id/c/f/b` = posthuman, rigor, idea_density, craft, form, brevity (0–5 each; weighted = 1.5×p + 1.5×r + the rest, max 35).
""", band_tables(rows, header, bands), "## Blurbs\n", "\n".join(blurbs), """
## Honorable mentions

Strong on some axes, weak on others; one line on the axis that cost them. All ten clear 20.0 and appear in the table above — they're singled out here because they're the stories people argue about.

""", "\n".join(near_lines), ""]
    return "\n".join(lines)


# ---------------------------------------------------------------- 04-prescience.md
def build_presc():
    nz = [e for e in presc if e.get("final", 0) > 0]
    nz.sort(key=lambda e: (-e["final"], -e["adjusted"], -e["raw_hits"]))
    rows = []
    for i, e in enumerate(nz, 1):
        prec = f"+{e['precision_bonus']}" if e["precision_bonus"] else "+0"
        pen = f"−{e['penalty']}" if e["penalty"] else "−0"
        rows.append(f"| {i} | [{esc(e['title'])}]({e['url']}) | {esc(e['author'])} | {e['year']} | {' '.join(e['tier_hits'])} | {e['raw_hits']} | {prec} | {pen} | {e['adjusted']} | ×{e['multiplier']} | **{fmt(e['final'])}** |")
    notes = []
    for i, e in enumerate(nz, 1):
        notes.append(f"{i}. **[{esc(e['title'])}]({e['url']})** — {e['justification']}")
    lines = f"""# Prescience — how well the old stories predicted 2022–2026

A second, independent pass over the survey: every story that could have been written *before* the AI era gets re-scored for how well it predicted what actually happened in AI 2022–2026. The full rubric lives in [`prescience_scoring_guide.txt`](prescience_scoring_guide.txt) — a 2022-style briefing document on the intervening years, plus the checklist the scoring uses. Stories posted after November 2022 are reportage, not prediction, and are excluded from this pass.

**Method (guide §9–§10):** each checklist hit scores Tier A ×5, Tier B ×3, Tier C ×1; a precision bonus of +0…+5 for naming real mechanisms (training, containment failure, institutional response) rather than just outcomes; −2 per anti-pattern fiction reliably gets wrong (the singular AI, overnight takeoff, embodiment-by-default, the never-wrong oracle…), floored at zero; then an era multiplier reflecting how hard the prediction was from that year — ×2.0 pre-2010, ×1.7 2010–14, ×1.4 2015–18, ×1.15 2019–21, ×1.0 2022+.

**Status:** oldest-first pass in progress — {len(presc)} of {len(scores)} stories prescience-scored so far; this table shows the {len(nz)} with a final score above zero. The {len(presc)-len(nz)} zero-scoring stories are omitted.

| Rank | Title | Author | Year | Tier hits | Raw | Prec | Pen | Adj | ×Era | **Final** |
|---|---|---|---|---|---|---|---|---|---|---|
{chr(10).join(rows)}

## Most prescient element / largest miss

{chr(10).join(notes)}
"""
    return lines


for path, content in [
    ("README.md", build_readme()),
    ("03-scores.md", build_scores()),
    ("04-shortlist.md", build_shortlist()),
    ("04-prescience.md", build_presc()),
]:
    with open(os.path.join(BASE, path), "w") as f:
        f.write(content if content.endswith("\n") else content + "\n")
    print(f"wrote {path} ({len(content)} bytes)")
