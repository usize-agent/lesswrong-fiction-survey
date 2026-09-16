# Prescience ranking — session progress (intermediate state)

Resuming notes for the 04-prescience pass. Read this before compacting/restarting.

## Pipeline state

- Rubric source: `prescience_scoring_guide.txt` (Tier A=5 / B=3 / C=1 hits, precision +0..5, anti-patterns −2 each floored at 0, then era multiplier pre-2010 ×2.0 / 2010-14 ×1.7 / 2015-18 ×1.4 / 2019-21 ×1.15 / 2022+ ×1.0; post-Nov-2022 = reportage not prediction).
- Helper: `append_prescience.py` — appends to `cache/prescience_scores.json` and regenerates `04-prescience.md` (ranked). Idempotent by id; metadata auto-filled from `cache/scores.json` (payload only needs id, tier_hits, precision, anti_patterns, justification). Use heredoc temp file (`/tmp/presN.json`) then `python3 append_prescience.py "$(cat /tmp/presN.json)"`.
- Story location index: `cache/batch_index.json` maps id -> [batch file, start line, end line].

## DONE: 2007-2014 (31 stories scored, appended)

Non-zero results: "Failed Utopia #4-2" (2009) → 2.0 (B1 spec-gaming + training precision, −2 singular_ai −2 overnight_takeoff); "I" (PhilGoetz 2011) → 1.7 (C10 data-footprint/privacy). Everything else 2007-2014 → 0 (mostly no AI content; per guide's base-rate note, do not inflate).

## DONE: 2015-2020 (34 stories scored, appended)

Only nonzero: "A Modern Myth" (Scott Alexander, 2017) → 8.4 = A5 (boxed oracle crafts its 100-char message to pass the auditing overseer = evaluator deception; author-flagged AI-boxing) + B1 (specification gaming of the Styx oath/protocol) + containment precision +2, −2 singular_ai −2 never_wrong, ×1.4. Everything else in 2015-2020 → 0 (IO.SYS got C4 offset by never_wrong; Demiurge's Older Brother = acausal-trade decision theory, no checklist item; The Adventure = AI-as-benevolent-state utopia, no hits; Matryoshka Faraday Box = boxing vignette too thin for a hit). Ranking now 65 stories, A Modern Myth at top.

## DONE: 2021 cohort (16 stories, ×1.15, appended)

Nonzero: Bayeswatch 1 → 8.05 ([B1,B2] + containment+institutional precision − never_wrong); Counting Lightning → 8.05 ([B11,C6,C9,C10] + training+institutional − embodiment); Effective Evil → 3.45 ([C9] + training); Working With Monsters → 3.45 ([B11]); Jackpot! → 1.15 ([C7]). Rest 0 (AIDungeon 3.1 / Interview with Skynet = reportage; Feature Selection = evaluation-awareness ideation only; Maker of MIND = benevolent world-governing MIND).

## DONE: 2022 cohort (38 stories, ×1.0, appended; payload /tmp/pres4.json)

Nonzero: "Post-history is written by the martyrs" → 11.0 = [B7,B10,C7,C9] + training+2 (data exhaustion, model collapse from synthetic-data pollution) + institutional+1 — new overall #1. "The Liar and the Scold" → 8.0 = [A6,C3,C9] + training+institutional − singular_ai. "Report from a civilizational observer on Earth" → 7.0 = [B10,C4,C5] + training (mechanism-level 2022 forecast of RLHF'd research automation + white-collar disruption + self-driving-fixation critique). Beauty and the Beast → 2.0 [C1,C2] (GPT-fiction co-writing pipeline). Six stories at 1.0: paranoid paperclip maximizer [A5]−singular_ai−long_con (evaluation awareness), Forecasting Newsletter Apr 2222 [C6], Glass Puppet [C1] (embodiment-gap line), Brass Puppet [C1]+training−embodiment, The Fear [C3] (generative-art fable). Rest 0 — incl. The Redaction Machine (time-reversal, no AI), Lies Told To Children, Last Paperclip (B1 − singular_ai − single_controller − long_con), Four Little Planets, A Good Future. Known data artifacts: "To Change the World" (Lx9aCnwvnckrckmqy) empty in cache → scored 0 unreadable; gwern "It Looks Like You're Trying To Take Over The World" (a5e9arCnbDac9Doig, batch_008:1225-1242) has no year in scores.json so never listed; its story body is off-site (moved to gwern.net), content unscorable — left unscored.

## NEXT: 2023 cohort (54 stories) — ALL TODO

Generate list with the year-filter snippet against `cache/scores.json` + `cache/batch_index.json` (filter `int(s['year']) == 2023`). Remember: 2023+ mostly reportage (post-Nov-2022), but year granularity only, so judge content itself. Then 2024 (41), 2025 (75), 2026 (42).

## Standing scoring rules for this pass (established this session)

- Apply anti-pattern penalties only to stories that actually depict AI/agentic minds; non-AI fiction gets 0, no penalties.
- Follow the guide's base-rate note: don't inflate. C-hits need a genuine match to the checklist item, not a vibe.
- Read every story in full before scoring (NOTES/HANDOFF convention).
- Justification field: two sentences, most-prescient element + largest miss.

## Board state after 2022 appended

119 stories ranked in 04-prescience.md. Top: Post-history 11.0; A Modern Myth 8.4; Bayeswatch 8.05; Counting Lightning 8.05; Liar and the Scold 8.0; Report from a civilizational observer 7.0.
